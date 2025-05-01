import asyncio
import os
from argparse import Namespace
from asyncio.queues import Queue

from common.file_ops.file_manager import FileManager, FileOperation
from common.flow_manager import FlowManager
from common.protocol.go_back_n import GoBackN
from common.protocol.protocol import Protocol
from common.protocol.stop_and_wait import StopAndWait
from common.skt.acceptor_socket import AcceptorSocket
from common.skt.connection_socket import ConnectionSocket
from common.skt.packet import HeaderFlags, Packet
from common.config import Config


class Server:
    def __init__(self, args: Namespace) -> None:
        self.config = Config(args)
        self.flow_manager = FlowManager()
        self.acceptor_skt = AcceptorSocket(self.config.protocol_type, self.flow_manager)

    async def start_server(self) -> None:
        self.acceptor_skt.bind(self.config.host, self.config.port)
        incoming_connections: Queue[ConnectionSocket] = asyncio.Queue()

        async def acceptor_callback() -> None:
            while True:
                connection_skt = await self.acceptor_skt.accept()
                await incoming_connections.put(connection_skt)

        async def handle_connection() -> None:
            while True:
                connection_skt = await incoming_connections.get()

                protocol: Protocol = self._init_protocol_for_connection(connection_skt)
                asyncio.create_task(protocol.handle_connection())

        acceptor_task = asyncio.create_task(acceptor_callback())
        handle_task = asyncio.create_task(handle_connection())

        await asyncio.gather(acceptor_task, handle_task)

    def run(self) -> None:
        if self.config.verbose:
            print("[Server] Starting server with the following parameters:")
            print(f"[Server] Host: {self.config.host}")
            print(f"[Server] Port: {self.config.port}")
            print(f"[Server] Storage folder dir path: {self.config.dirpath}")
            print(f"[Server] Protocol: {self.config.protocol_type}")

        loop = asyncio.get_event_loop()

        try:
            loop.run_until_complete(self.start_server())
        except KeyboardInterrupt:
            print("\n[Server] Stopping server...")

            tasks = [t for t in asyncio.all_tasks(loop=loop) if not t.done()]
            for task in tasks:
                task.cancel()

            loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        finally:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()

    async def _handle_download(self, protocol: Protocol) -> None:
        try:
            request_packet = await protocol.socket.recv()
            filename = request_packet.get_data().decode().strip()

            file_manager = FileManager(
                self.config.dirpath, filename, FileOperation.READ
            )

            print(f"[Server] Sending file {filename} to user")
            await protocol.send_file(file_manager, HeaderFlags.DOWNLOAD.value)

        except FileNotFoundError | FileExistsError:
            fin_pkt = Packet(
                flags=self.config.protocol_type.value | HeaderFlags.FIN.value,
            )
            await protocol.socket.send(fin_pkt)

    async def _handle_upload(self, protocol: Protocol) -> None:
        try:
            name_packet = await protocol.socket.recv()
            filename = name_packet.get_data().decode().strip()

            if not self._is_valid_filename(filename):
                error_pkt = Packet(
                    0,
                    0,
                    b"Invalid filename",
                    self.protocol_flag.value | HeaderFlags.FIN.value,
                )
                await protocol.socket.send(error_pkt)
                return

            storage_path = os.path.join(self.dirpath, "storage")
            os.makedirs(storage_path, exist_ok=True)

            print(f"[Server] Receiving file {filename} from client")
            await protocol.recv_file(filename, storage_path, HeaderFlags.UPLOAD.value)
            print(f"[Server] File {filename} received successfully")

        except Exception as e:
            print(f"[Server] Error handling upload: {e}")
            raise

    def _is_valid_filename(self, filename: str) -> bool:
        """Validate filename to prevent path traversal."""
        return bool(
            filename
            and not os.path.isabs(filename)
            and not any(c in filename for c in "/\\")
        )

    def _init_protocol_for_connection(self, conn: ConnectionSocket) -> Protocol:
        match self.config.protocol_type:
            case HeaderFlags.STOP_WAIT:
                return StopAndWait(conn, self.config)
            case HeaderFlags.GBN:
                return GoBackN(conn, self.config)
            case _:
                raise ValueError(f"Unsupported protocol: {self.config.protocol_type}")
