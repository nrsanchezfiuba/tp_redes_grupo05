import asyncio
import os
from argparse import Namespace

from common.protocol.stop_and_wait import StopAndWait
from common.skt.connection_socket import ConnectionSocket
from common.skt.packet import HeaderFlags

protocol_mapping = {
    "SW": HeaderFlags.STOP_WAIT,
    "GBN": HeaderFlags.GBN,
}


class Client:
    def __init__(self, args: Namespace) -> None:
        self.args: Namespace = args
        self.host: str = args.host
        self.port: int = args.port
        self.dst: str = args.dst
        self.name: str = args.name
        self.protocol: str = args.protocol.upper()
        self.verbose: bool = args.verbose
        self.quiet: bool = args.quiet
        self.file_path = os.path.join(self.dst, self.name)

        self.protocol_flag = protocol_mapping[self.protocol]

    async def start_client(self) -> None:
        print(f"[Client] Connecting to {self.host}:{self.port}")

        connection_skt = ConnectionSocket.for_client((self.host, self.port))
        await connection_skt.connect(self.protocol_flag)

        await self.handle_download(connection_skt)

    async def handle_download(self, connection_skt: ConnectionSocket) -> None:
        protocol = StopAndWait(connection_skt)
        await protocol.recv_file(self.name, self.dst, HeaderFlags.DOWNLOAD.value)

    async def handle_upload(self, connection_skt: ConnectionSocket) -> None:
        pass

    def run(self) -> None:
        if self.verbose:
            print("Starting client with the following parameters:")
            print(f"Host: {self.host}")
            print(f"Port: {self.port}")
            print(f"Destination path: {self.dst}")
            print(f"Filename: {self.name}")
            print(f"Protocol: {self.protocol}")
        elif self.quiet:
            pass
        else:
            print("Starting client...")

        # asyncio.run(self.start_client())

        loop = asyncio.get_event_loop()

        try:
            loop.run_until_complete(self.start_client())
        except KeyboardInterrupt:
            print("\n[Client] Stopping client...")

            tasks = [t for t in asyncio.all_tasks(loop=loop) if not t.done()]
            for task in tasks:
                task.cancel()

            loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        finally:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()
