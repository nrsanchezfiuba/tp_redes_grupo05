import asyncio
from typing import Optional, Tuple

from common.skt.packet import Packet
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
