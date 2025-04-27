import asyncio
from typing import Optional, Tuple

from common.skt.packet import HeaderFlags, Packet
from common.skt.udp_socket import UDPSocket


class ConnectionSocket:

    @classmethod
    def for_client(cls, addr: Tuple[str, int]) -> "ConnectionSocket":
        return cls(addr, None)

    @classmethod
    def for_server(
        cls, addr: Tuple[str, int], queue: asyncio.Queue[Packet]
    ) -> "ConnectionSocket":
        return cls(addr, queue)

    def __init__(self, addr: Tuple[str, int], queue: Optional[asyncio.Queue[Packet]]):
        self.addr: Tuple[str, int] = addr
        self.udp_socket: UDPSocket = UDPSocket()
        self.queue: Optional[asyncio.Queue[Packet]] = queue

    async def init_connection(
        self, protocol: HeaderFlags = HeaderFlags.STOP_WAIT
    ) -> None:
        await self.udp_socket.init_connection(self.addr[0], self.addr[1])
        await self.udp_socket.send_all(
            Packet(flags=HeaderFlags.SYN.value | protocol.value).to_bytes(), self.addr
        )
        response, _ = await self.udp_socket.recv_all()
        print(f"[ConnectionSocket] Received packet: {response.decode('utf-8')}")
        pkt = Packet.from_bytes(response)
        if pkt.is_syn() and pkt.is_ack():
            print(f"[ConnectionSocket] Connection established with {self.addr}")
        else:
            raise RuntimeError(
                f"[ConnectionSocket] Failed to establish connection with {self.addr}"
            )

    async def send(self, packet: Packet) -> None:
        await self.udp_socket.send_all(packet.to_bytes(), self.addr)

    async def recv(self) -> Packet:
        recv_pkt = None

        if not self.queue:
            response, _ = await self.udp_socket.recv_all()
            recv_pkt = Packet.from_bytes(response)
        else:
            recv_pkt = await self.queue.get()

        return recv_pkt

    async def close(self) -> None:
        # We pray to garbage collector
        # await self.queue.shutdown(immediate=True)
        pass
