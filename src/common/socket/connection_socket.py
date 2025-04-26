import asyncio
from typing import Tuple

from common.socket.packet import Packet
from common.socket.udp_socket import UDPSocket


class ConnectionSocket:

    def __init__(self, host: str, port: int, queue: asyncio.Queue[Packet]):
        self.addr: Tuple[str, int] = (host, port)
        self.udp_socket: UDPSocket = UDPSocket()
        self.queue: asyncio.Queue[Packet] = queue

    async def send(self, packet: Packet) -> None:
        await self.udp_socket.send_all(packet.to_bytes(), self.addr)

    async def recv(self) -> Packet:
        recv_pkt = await self.queue.get()
        return recv_pkt

    async def close(self) -> None:
        # We pray to garbage collector
        # await self.queue.shutdown(immediate=True)
        pass
