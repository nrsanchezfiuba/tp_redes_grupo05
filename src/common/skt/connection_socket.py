import asyncio
from typing import Optional, Tuple

from common.skt.packet import HeaderFlags, Packet
from common.skt.udp_socket import UDPSocket

MAX_CONNECT_RETYRIES: int = 3
MAX_CONNECT_TIMEOUT: float = 5.0


class ConnectionSocket:
    @classmethod
    def for_client(cls, addr: Tuple[str, int]) -> "ConnectionSocket":
        return cls(addr, None)

    @classmethod
    async def for_server(
        cls, addr: Tuple[str, int], queue: asyncio.Queue[Packet]
    ) -> "ConnectionSocket":
        return cls(addr, queue)

    def __init__(self, addr: Tuple[str, int], queue: Optional[asyncio.Queue[Packet]]):
        self.addr: Tuple[str, int] = addr
        self.udp_socket: UDPSocket = UDPSocket()
        self.queue: Optional[asyncio.Queue[Packet]] = queue
        self.timer: None
        self.connect_retries: int = 0
        self.protocol: HeaderFlags = HeaderFlags.SYN

    async def connect(self, protocol: HeaderFlags) -> None:
        self.protocol = protocol
        await self.send(Packet(flags=HeaderFlags.SYN.value | protocol.value))

        # Timeout only for the connection phase
        try:
            # Wait for SYN-ACK with a timeout
            pkt = await asyncio.wait_for(self.recv(), timeout=MAX_CONNECT_TIMEOUT)
            if pkt.is_syn() and pkt.is_ack():
                print(f"Connected to {self.addr}")
                return
            else:
                raise RuntimeError("Invalid handshake response")
        except asyncio.TimeoutError:
            self.connect_retries += 1
            if self.connect_retries > MAX_CONNECT_RETYRIES:
                raise TimeoutError(
                    f"Connection failed after {MAX_CONNECT_RETYRIES} retries"
                )
            print(f"Retrying... (Attempt {self.connect_retries})")
            return await self.connect(protocol)  # Retry

    async def send(self, packet: Packet) -> None:
        await self.udp_socket.send_all(packet.to_bytes(), self.addr)

    async def recv(self) -> Packet:
        recv_pkt = None

        if not self.queue:
            response, _ = await self.udp_socket.recv_all()
            recv_pkt = Packet.from_bytes(response)
        else:
            recv_pkt = await self.queue.get()

        print(f"[ConnectionSocket] Received packet: {recv_pkt}")
        return recv_pkt

    async def close(self) -> None:
        pass
