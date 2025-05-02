import asyncio
from abc import ABC, abstractmethod

from common.config import Config
from common.file_ops.file_manager import FileManager, FileOperation
from common.skt.connection_socket import ConnectionSocket
from common.skt.packet import HeaderFlags, Packet

TIMEOUT_END_CONECTION: float = 5
INITIAL_RETRIES: int = 5


class Protocol(ABC):
    def __init__(self, socket: ConnectionSocket):
        self.socket = socket

    @classmethod
    def from_connection(cls, conn: ConnectionSocket, config: Config) -> "Protocol":
        # In-line import to avoid circular dependency
        from common.protocol.go_back_n import GoBackN
        from common.protocol.stop_and_wait import StopAndWait

        match config.protocol_type:
            case HeaderFlags.SW:
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

    @abstractmethod
    async def recv_file(self, file_manager: FileManager, mode: int) -> None:
        raise NotImplementedError("Must implement recv_file method")

    @abstractmethod
    async def send_file(self, file_manager: FileManager, mode: int) -> None:
        raise NotImplementedError("Must implement send_file method")

    async def _initiate_transaction(self, config: Config) -> None:
        file_name_pkt = Packet(
            data=config.client_filename.encode(),
            flags=config.protocol_type.value | config.client_mode.value,
        )
        retries = 0
        while retries < INITIAL_RETRIES:
            try:
                await self.socket.send(file_name_pkt)
                ack_pkt = await asyncio.wait_for(self.socket.recv(), timeout=1.0)
                if ack_pkt.is_ack():
                    break
                retries += 1
            except asyncio.TimeoutError:
                pass

            await asyncio.sleep(0.5)
        if retries == INITIAL_RETRIES:
            fin_pkt = Packet(
                flags=HeaderFlags.SW.value
                | HeaderFlags.FIN.value
                | config.client_mode.value,
            )
            await self.socket.send(fin_pkt)
            raise TimeoutError("Failed to receive ACK for filename packet")

        match config.client_mode:
            case HeaderFlags.UPLOAD:
                file_manager = FileManager(
                    config.client_dst,
                    config.client_filename,
                    FileOperation.READ,
                )
                await self.send_file(file_manager, config.client_mode.value)
            case HeaderFlags.DOWNLOAD:
                file_manager = FileManager(
                    config.client_dst,
                    config.client_filename,
                    FileOperation.WRITE,
                )
                await self.recv_file(file_manager, config.client_mode.value)
            case _:
                raise ValueError(f"Invalid mode in packet {config.client_mode}")

    async def _handle_connection(self, config: Config) -> None:
        file_name_pkt = await self.socket.recv()
        mode = file_name_pkt.get_mode()
        file_name = file_name_pkt.get_data().decode().strip()
        if file_name_pkt.get_protocol_type() != config.protocol_type:
            fin_pkt = Packet(
                flags=config.protocol_type.value | HeaderFlags.FIN.value | mode.value,
            )
            await self.socket.send(fin_pkt)
            return
        try:
            match mode:
                case HeaderFlags.UPLOAD:
                    file_manager = FileManager(
                        config.server_dirpath, file_name, FileOperation.WRITE
                    )
                    ack = Packet(
                        ack_num=file_name_pkt.get_seq_num(),
                        flags=config.protocol_type.value
                        | HeaderFlags.ACK.value
                        | mode.value,
                    )
                    await self.socket.send(ack)
                    await self.recv_file(file_manager, mode.value)
                case HeaderFlags.DOWNLOAD:
                    file_manager = FileManager(
                        config.server_dirpath, file_name, FileOperation.READ
                    )
                    ack = Packet(
                        ack_num=file_name_pkt.get_seq_num(),
                        flags=config.protocol_type.value
                        | HeaderFlags.ACK.value
                        | file_name_pkt.get_mode().value,
                    )
                    await self.socket.send(ack)
                    await self.send_file(file_manager, mode.value)
                case _:
                    raise ValueError("Invalid mode in packet")
        except FileNotFoundError:
            print(f"[ERROR] File not found: {file_name}")
            fin_pkt = Packet(
                config.protocol_type.value | HeaderFlags.FIN.value,
            )
            await self.socket.send(fin_pkt)
