from abc import ABC, abstractmethod

from common.skt.connection_socket import ConnectionSocket
from common.skt.packet import HeaderFlags

protocol_mapping = {
    "SW": HeaderFlags.STOP_WAIT,
    "GBN": HeaderFlags.GBN,
}

mode_mapping = {
    "upload": HeaderFlags.UPLOAD,
    "download": HeaderFlags.DOWNLOAD,
}

BLOCK_SIZE = 1000


class Protocol(ABC):
    def __init__(self, socket: ConnectionSocket):
        self.socket = socket

    @abstractmethod
    def save_data(self, data: bytes) -> None:
        pass

    @abstractmethod
    async def recv_file(self, name: str, dirpath: str, mode: int) -> None:
        pass

    @abstractmethod
    async def send_file(self, name: str, filepath: str, mode: int) -> None:
        pass
