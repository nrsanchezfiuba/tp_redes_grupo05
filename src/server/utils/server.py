import asyncio
import os
from argparse import Namespace

from common.flow_manager import FlowManager
from common.protocol.protocol import Protocol
from common.skt.acceptor_socket import AcceptorSocket
from common.skt.packet import HeaderFlags


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

        header_flag = HeaderFlags.STOP_WAIT

        if self.protocol == "SW":
            header_flag = HeaderFlags.STOP_WAIT
        elif self.protocol == "GBN":
            header_flag = HeaderFlags.GBN
        else:
            raise ValueError("I dont have this protocol")

        self.flow_manager = FlowManager()
        self.acceptor_skt = AcceptorSocket(header_flag, self.flow_manager)

    async def start_server(self) -> None:
        while True:
            await self.acceptor_skt.bind(self.host, self.port)
            protocol, mode = await self.acceptor_skt.accept()
            if mode == HeaderFlags.DOWNLOAD:
                asyncio.run(self._handle_download(protocol))
            elif mode == HeaderFlags.UPLOAD:
                asyncio.run(self._handle_upload(protocol))

    def run(self) -> None:
        if self.verbose:
            print("Starting server with the following parameters:")
            print(f"Host: {self.host}")
            print(f"Port: {self.port}")
            print(f"Storage folder dir path: {self.dirpath}")
            print(f"Protocol: {self.protocol}")
        elif self.quiet:
            pass  # Suppress output
        else:
            print("Starting server...")

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
        await protocol.recv_file("", self.dirpath, HeaderFlags.DOWNLOAD.value)

    async def _handle_upload(self, protocol: Protocol) -> None:
        pass
