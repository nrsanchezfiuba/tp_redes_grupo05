from abc import ABC, abstractmethod

from common.udp_socket import UDPSocket

BLOCK_SIZE = 1000


class Protocol(ABC):
    def __init__(self, socket: UDPSocket):
        self.socket = socket

    @staticmethod
    def save_data(data: bytes, filename: str) -> None:
        with open(filename, "ab") as file:
            file.write(data)

    @abstractmethod
    async def recv_file(self, name: str, dirpath: str, mode: int) -> None:
        pass

    @abstractmethod
    async def send_file(self, name: str, filepath: str, mode: int) -> None:
        pass
