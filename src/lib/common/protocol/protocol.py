import asyncio
from abc import ABC, abstractmethod

from lib.common.config import Config
from lib.common.file_ops.file_manager import FileManager, FileOperation
from lib.common.logger import Logger
from lib.common.skt.connection_socket import ConnectionSocket
from lib.common.skt.packet import HeaderFlags, Packet

TIMEOUT_INTERVAL: float = 0.01
RETRANSMISSION_RETRIES: int = 10


class Protocol(ABC):
    def __init__(
        self, socket: ConnectionSocket, config: Config, logger: Logger
    ) -> None:
        self.socket = socket
        self.config = config
        self.logger: Logger = logger
        self.mode: HeaderFlags = HeaderFlags.NONE

    @classmethod
    def from_connection(
        cls, conn: ConnectionSocket, config: Config, logger: Logger
    ) -> "Protocol":
        # In-line import to avoid circular dependency
        from lib.common.protocol.go_back_n import GoBackN
        from lib.common.protocol.stop_and_wait import StopAndWait

        match config.protocol_type:
            case HeaderFlags.SW:
                return StopAndWait(conn, config, logger)
            case HeaderFlags.GBN:
                return GoBackN(conn, config, logger)
            case _:
                raise ValueError("Invalid protocol type")

    @abstractmethod
    async def recv_file(self, file_manager: FileManager) -> None:
        raise NotImplementedError("Must implement recv_file method")

    @abstractmethod
    async def send_file(self, file_manager: FileManager) -> None:
        raise NotImplementedError("Must implement send_file method")

    async def initiate_transaction(self) -> None:
        file_name_pkt = Packet(
            data=self.config.client_filename.encode(),
            flags=self.config.protocol_type.value | self.config.client_mode.value,
        )

        for _ in range(RETRANSMISSION_RETRIES):
            try:
                await self.socket.send(file_name_pkt)
                ack_pkt = await asyncio.wait_for(
                    self.socket.recv(), timeout=TIMEOUT_INTERVAL
                )

                if self.socket.is_closed():
                    return

                if ack_pkt.is_ack() or ack_pkt.get_length() > 0:
                    break
            except asyncio.TimeoutError:
                pass

            await asyncio.sleep(0.5)
        else:
            await self.socket.disconnect()
            raise TimeoutError("Failed to receive ACK for filename packet")

        self.mode = self.config.client_mode
        file_manager = FileManager(
            self.config.client_dst,
            self.config.client_filename,
            (
                FileOperation.READ
                if self.mode == HeaderFlags.UPLOAD
                else FileOperation.WRITE
            ),
        )

        if self.mode == HeaderFlags.UPLOAD:
            await self.send_file(file_manager)
        elif self.mode == HeaderFlags.DOWNLOAD:
            await self.recv_file(file_manager)
        else:
            raise ValueError(f"Invalid mode in packet {self.config.client_mode}")

    async def handle_connection(self) -> None:
        for _ in range(RETRANSMISSION_RETRIES):
            try:
                file_name_pkt = await asyncio.wait_for(
                    self.socket.recv(), timeout=TIMEOUT_INTERVAL
                )

                if self.socket.is_closed():
                    return

                if file_name_pkt.get_protocol_type() != self.config.protocol_type:
                    await self.socket.disconnect()
                    return

                file_name = file_name_pkt.get_data().decode().strip()
                self.mode = file_name_pkt.get_mode()

                ack = Packet(
                    flags=self.config.protocol_type.value
                    | HeaderFlags.ACK.value
                    | self.mode.value,
                )
                await self.socket.send(ack)
                break
            except asyncio.TimeoutError:
                pass

            await asyncio.sleep(0.5)
        else:
            self.logger.error("Failed to receive file name packet")
            await self.socket.disconnect()
            return

        try:
            file_manager = FileManager(
                self.config.server_dirpath,
                file_name,
                (
                    FileOperation.WRITE
                    if self.mode == HeaderFlags.UPLOAD
                    else FileOperation.READ
                ),
            )

            if self.mode == HeaderFlags.UPLOAD:
                await self.recv_file(file_manager)
            elif self.mode == HeaderFlags.DOWNLOAD:
                await self.send_file(file_manager)
            else:
                raise ValueError("Invalid mode in packet")
        except FileNotFoundError:
            self.logger.error("File not found")
            await self.socket.disconnect()
