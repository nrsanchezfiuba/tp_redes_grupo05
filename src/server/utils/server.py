import asyncio
import os
from argparse import Namespace
from asyncio.queues import Queue

from common.flow_manager import FlowManager
from common.protocol.protocol import Protocol
from common.protocol.stop_and_wait import StopAndWait
from common.skt.acceptor_socket import AcceptorSocket
from common.skt.connection_socket import ConnectionSocket
from common.skt.packet import HeaderFlags, Packet

protocol_mapping = {
    "SW": HeaderFlags.STOP_WAIT,
    "GBN": HeaderFlags.GBN,
}


class Server:
    def __init__(self, args: Namespace) -> None:
        self.args: Namespace = args
        self.host: str = args.host
        self.port: int = args.port
        self.dirpath: str = args.storage
        self.protocol: str = args.protocol.upper()
        self.verbose: bool = args.verbose
        self.quiet: bool = args.quiet

        # Initialize the dirpath folder path
        if not self.dirpath:
            self.dirpath = os.path.join(os.path.dirname(__file__), "dirpath")
        os.makedirs(self.dirpath, exist_ok=True)

        self.header_flag = protocol_mapping.get(self.protocol)
        if self.header_flag is None:
            raise ValueError(f"Unsupported protocol: {self.protocol}")

        self.flow_manager = FlowManager()
        self.acceptor_skt = AcceptorSocket(self.header_flag, self.flow_manager)

    async def start_server(self) -> None:
        self.acceptor_skt.bind(self.host, self.port)
        incomming_connections: Queue[ConnectionSocket] = asyncio.Queue()

        async def acceptor_callback() -> None:
            while True:
                connection_skt = await self.acceptor_skt.accept()
                await incomming_connections.put(connection_skt)

        async def handle_connection() -> None:
            while True:
                connection_skt = await incomming_connections.get()
                protocol = StopAndWait(connection_skt, self.verbose)
                await self._handle_download(protocol)

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

            storage_path = os.path.join(self.dirpath, "storage")
            filepath = os.path.join(storage_path, filename)

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
            await protocol.send_file(filename, storage_path, HeaderFlags.DOWNLOAD.value)

        except Exception as e:
            print(f"[Server] Error handling download: {e}")
            raise

    async def _handle_upload(self, protocol: Protocol) -> None:
        pass
