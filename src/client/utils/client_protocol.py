import asyncio
from typing import Tuple


class ClientProtocol(asyncio.DatagramProtocol):
    def __init__(self) -> None:
        self.queue: asyncio.Queue[Tuple[bytes, Tuple[str, int]]] = asyncio.Queue()

    def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:
        self.queue.put_nowait((data, addr))

    async def recv(self) -> Tuple[bytes, Tuple[str, int]]:
        return await self.queue.get()
