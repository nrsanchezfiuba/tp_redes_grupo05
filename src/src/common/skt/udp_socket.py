import asyncio
import socket
from typing import Tuple


class UDPSocket:
    def __init__(self) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(False)

    def __del__(self) -> None:
        self.sock.close()

    def bind(self, host: str, port: int) -> None:
        self.sock.bind((host, port))

    async def recv_all(self) -> Tuple[bytes, Tuple[str, int]]:
        loop = asyncio.get_running_loop()
        data, addr = await loop.sock_recvfrom(self.sock, 2048)
        return data, addr

    async def send_all(self, data: bytes, addr: Tuple[str, int]) -> None:
        loop = asyncio.get_running_loop()
        await loop.sock_sendto(self.sock, data, addr)
