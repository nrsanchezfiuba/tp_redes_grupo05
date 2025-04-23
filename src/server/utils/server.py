import asyncio
import os
from argparse import Namespace

from common.udp_socket import UDPSocket


class Server:
    def __init__(self, args: Namespace) -> None:
        self.args: Namespace = args
        self.host: str = args.host
        self.port: int = args.port
        self.storage: str = args.storage
        self.protocol: str = args.protocol.upper()
        self.verbose: bool = args.verbose
        self.quiet: bool = args.quiet

        # Initialize the storage folder path
        if not self.storage:
            self.storage = os.path.join(os.path.dirname(__file__), "storage")
        os.makedirs(self.storage, exist_ok=True)

        self.socket = UDPSocket()

    async def start_server(self) -> None:
        await self.socket.init_connection(self.host, self.port)
        if not self.quiet:
            print(
                f"Server listening on {self.host}:{self.port} using {self.protocol} protocol"
            )

        while True:
            data, addr = await self.socket.recv_all()

            if self.verbose:
                print(f"Received {len(data)} bytes from {addr}")

            response = f"OKA - {data.decode()}"
            self.socket.send_all(response.encode(), addr)

    def run(self) -> None:
        if self.verbose:
            print("Starting server with the following parameters:")
            print(f"Host: {self.host}")
            print(f"Port: {self.port}")
            print(f"Storage folder dir path: {self.storage}")
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
            tasks = asyncio.all_tasks(loop=loop)
            for task in tasks:
                if task is not asyncio.current_task():
                    task.cancel()
            loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        finally:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()
