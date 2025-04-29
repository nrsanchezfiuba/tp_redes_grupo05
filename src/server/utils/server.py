import asyncio
import os
from argparse import Namespace
from asyncio.queues import Queue

from common.flow_manager import FlowManager
from common.protocol.go_back_n import GoBackN
from common.protocol.protocol import Protocol, protocol_mapping
from common.protocol.stop_and_wait import StopAndWait
from common.skt.acceptor_socket import AcceptorSocket
from common.skt.connection_socket import ConnectionSocket
from common.skt.packet import HeaderFlags, Packet


class Server:
    def __init__(self, args: Namespace) -> None:
        self.args: Namespace = args
        self.host: str = args.host
        self.port: int = args.port
        self.dirpath: str = args.storage
        self.protocol: str = args.protocol.upper()
        self.verbose: bool = args.verbose
        self.quiet: bool = args.quiet

        if not self.dirpath:
            self.dirpath = os.path.join(os.path.dirname(__file__), self.dirpath)
        os.makedirs(self.dirpath, exist_ok=True)

        self.header_flag = protocol_mapping.get(self.protocol)
        if self.header_flag is None:
            raise ValueError(f"Unsupported protocol: {self.protocol}")

        self.flow_manager = FlowManager()
        self.acceptor_skt = AcceptorSocket(self.header_flag, self.flow_manager)

    async def start_server(self) -> None:
        self.acceptor_skt.bind(self.host, self.port)
        incoming_connections: Queue[ConnectionSocket] = asyncio.Queue()

        async def acceptor_callback() -> None:
            while True:
                connection_skt = await self.acceptor_skt.accept()
                await incoming_connections.put(connection_skt)

        async def handle_connection() -> None:
            while True:
                connection_skt = await incoming_connections.get()

                protocol: Protocol = GoBackN(connection_skt, self.verbose)

                if self.protocol == "SW":
                    protocol = StopAndWait(connection_skt, self.verbose)
                elif self.protocol == "GBN":
                    protocol = GoBackN(connection_skt, self.verbose)

                mode_packet = await connection_skt.recv()

                if mode_packet.get_mode() == HeaderFlags.UPLOAD:
                    asyncio.create_task(self._handle_upload(protocol))
                elif mode_packet.get_mode() == HeaderFlags.DOWNLOAD:
                    asyncio.create_task(self._handle_download(protocol))

        acceptor_task = asyncio.create_task(acceptor_callback())
        handle_task = asyncio.create_task(handle_connection())

        await asyncio.gather(acceptor_task, handle_task)

    def run(self) -> None:
        if self.verbose:
            print("[Server] Starting server with the following parameters:")
            print(f"[Server] Host: {self.host}")
            print(f"[Server] Port: {self.port}")
            print(f"[Server] Storage folder dir path: {self.dirpath}")
            print(f"[Server] Protocol: {self.protocol}")

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

            filepath = os.path.join(self.dirpath, filename)

            if not os.path.isfile(filepath):
                print(f"[Server] File {filename} not found, sending FIN")
                fin_pkt = Packet(
                    0,
                    0,
                    b"File not found",
                    HeaderFlags.STOP_WAIT.value | HeaderFlags.FIN.value,
                )
                await protocol.socket.send(fin_pkt)
                return

            print(f"[Server] Sending file {filename} to user")
            await protocol.send_file(filename, self.dirpath, HeaderFlags.DOWNLOAD.value)

        except Exception as e:
            print(f"[Server] Error handling download: {e}")
            raise

    async def _handle_upload(self, protocol: Protocol) -> None:
        try:
            name_packet = await protocol.socket.recv()
            filename = name_packet.get_data().decode().strip()

            if not self._is_valid_filename(filename):
                error_pkt = Packet(
                    0,
                    0,
                    b"Invalid filename",
                    HeaderFlags.STOP_WAIT.value | HeaderFlags.FIN.value,
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
