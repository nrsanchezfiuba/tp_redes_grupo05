from abc import ABC, abstractmethod

from common.config import Config
from common.file_ops.file_manager import FileManager
from common.skt.connection_socket import ConnectionSocket
from common.skt.packet import HeaderFlags


class Protocol(ABC):
    def __init__(self, socket: ConnectionSocket):
        self.socket = socket

    @classmethod
    def from_connection(cls, conn: ConnectionSocket, config: Config) -> "Protocol":
        from common.protocol.go_back_n import GoBackN
        from common.protocol.stop_and_wait import StopAndWait

        match config.protocol_type:
            case HeaderFlags.STOP_WAIT:
                return StopAndWait(conn, config)
            case HeaderFlags.GBN:
                return GoBackN(conn, config)
            case _:
                raise ValueError("Invalid protocol type")

    @abstractmethod
    async def initiate_transaction(self) -> None:
        raise NotImplementedError("Must implement initiate_transaction method")

    @abstractmethod
    async def handle_connection(self) -> None:
        raise NotImplementedError("Must implement handle_connection method")

    async def recv_file(self, file_manager: FileManager, mode: int) -> None:
        raise NotImplementedError("Must implement recv_file method")

    async def send_file(self, file_manager: FileManager, mode: int) -> None:
        raise NotImplementedError("Must implement send_file method")
