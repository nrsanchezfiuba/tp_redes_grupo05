from abc import ABC, abstractmethod

from common.file_ops.file_manager import FileManager
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
    async def initiate_transaction(self, file_name: str, mode: HeaderFlags) -> None:
        raise NotImplementedError("Must implement initiate_transaction method")

    @abstractmethod
    async def handle_connection(self) -> None:
        raise NotImplementedError("Must implement handle_connection method")

    @abstractmethod
    def save_data(self, data: bytes) -> None:
        raise NotImplementedError("Must implement save_data method")

    async def recv_file(self, file_manager: FileManager, mode: int) -> None:
        raise NotImplementedError("Must implement recv_file method")

    async def send_file(self, file_manager: FileManager, mode: int) -> None:
        raise NotImplementedError("Must implement send_file method")
