from abc import ABC, abstractmethod

from common.socket.connection_socket import ConnectionSocket

BLOCK_SIZE = 1000


class Protocol(ABC):
    def __init__(self, socket: ConnectionSocket):
        self.socket = socket

    @staticmethod
    def save_data(data: bytes, filename: str) -> None:
        print(f"[Protocol] Saving data to {filename}, {data.decode('utf-8')}")
        # with open(filename, "ab") as file:
        #     file.write(data)

    @abstractmethod
    async def recv_file(self, name: str, dirpath: str, mode: int) -> None:
        pass

    @abstractmethod
    async def send_file(self, name: str, filepath: str, mode: int) -> None:
        pass
