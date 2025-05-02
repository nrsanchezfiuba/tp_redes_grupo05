import asyncio
from typing import Optional, Tuple

from lib.common.logger import Logger
from lib.common.skt.packet import HeaderFlags, Packet
from lib.common.skt.udp_socket import UDPSocket

HANDSHAKE_TIMEOUT_INTERVAL: float = 1.5
HANDSHAKE_RETRIES: int = 5


class ConnectionSocket:
    @classmethod
    def for_client(
        cls, addr: Tuple[str, int], protocol: HeaderFlags, logger: Logger
    ) -> "ConnectionSocket":
        return cls(addr, None, protocol, logger)

    @classmethod
    async def for_server(
        cls,
        addr: Tuple[str, int],
        queue: asyncio.Queue[Packet],
        protocol: HeaderFlags,
        logger: Logger,
    ) -> "ConnectionSocket":
        return cls(addr, queue, protocol, logger)

    def __init__(
        self,
        addr: Tuple[str, int],
        queue: Optional[asyncio.Queue[Packet]],
        protocol: HeaderFlags,
        logger: Logger,
    ):
        self.addr: Tuple[str, int] = addr
        self.protocol: HeaderFlags = protocol
        self.udp_socket: UDPSocket = UDPSocket()
        self.queue: Optional[asyncio.Queue[Packet]] = queue
        self.closed: bool = False
        self.logger: Logger = logger

    async def connect(self) -> None:
        for attempt in range(HANDSHAKE_RETRIES):
            await self.send(Packet(flags=HeaderFlags.SYN.value | self.protocol.value))
            try:
                pkt = await asyncio.wait_for(
                    self.recv(), timeout=HANDSHAKE_TIMEOUT_INTERVAL
                )
                if pkt.is_syn() and pkt.is_ack():
                    self.logger.debug(
                        f"[ConnectionSocket] Connection established with {self.addr}"
                    )
                    break
                elif pkt.is_fin():
                    self.logger.debug(
                        f"[ConnectionSocket] Connection closed by {self.addr}"
                    )
                    break
            except TimeoutError:
                self.logger.debug(f"[ConnectionSocket] Retrying... (Attempt {attempt})")
                await asyncio.sleep(0.5)
        else:
            raise TimeoutError(
                f"[ConnectionSocket] Failed to establish connection with {self.addr}"
            )

    async def send(self, packet: Packet) -> None:
        if self.closed:
            raise RuntimeError("[ConnectionSocket] Cannot send on a closed socket")
        await self.udp_socket.send_all(packet.to_bytes(), self.addr)

    async def recv(self) -> Packet:
        if self.closed:
            raise RuntimeError("[ConnectionSocket] Cannot receive on a closed socket")

        recv_pkt = None
        if not self.queue:
            response, _ = await self.udp_socket.recv_all()
            recv_pkt = Packet.from_bytes(response)
        else:
            recv_pkt = await self.queue.get()

        if recv_pkt.is_fin():
            self.logger.debug(
                f"[ConnectionSocket] Received FIN packet from {self.addr}"
            )
            if not recv_pkt.is_ack():
                fin_ack = Packet(
                    flags=self.protocol.value
                    | HeaderFlags.FIN.value
                    | HeaderFlags.ACK.value
                )
                await self.send(fin_ack)
            self.closed = True

        self.logger.debug(f"[ConnectionSocket] Received packet: {recv_pkt}")
        return recv_pkt

    async def disconnect(self, retries: int = 5, timeout: float = 1.0) -> None:
        if self.closed:
            return

        fin = Packet(flags=self.protocol.value | HeaderFlags.FIN.value)

        for _ in range(retries):
            await self.send(fin)

            try:
                response = await asyncio.wait_for(self.recv(), timeout=timeout)
                if response.is_fin() and response.is_ack():
                    break
            except asyncio.TimeoutError:
                continue

        self.closed = True

    def is_closed(self) -> bool:
        return self.closed
