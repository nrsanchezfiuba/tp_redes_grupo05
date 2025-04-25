import asyncio
import os
from argparse import Namespace

from client.utils.client_protocol import ClientProtocol


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

    def handle_upload(self) -> None:
        self.run()

    def handle_download(self) -> None:
        self.run()

    async def start_client(self) -> None:
        print(f"[Client] Connecting to {self.host}:{self.port}")

        # la magia de concurrencia epica
        loop = asyncio.get_running_loop()
        protocol = ClientProtocol()
        transport, _ = await loop.create_datagram_endpoint(
            lambda: protocol, remote_addr=(self.host, self.port)
        )

        try:
            for i in range(5):
                message = f"Test message {i + 1}".encode()
                if self.verbose:
                    print(f"[Client] Sending: {message.decode()}")
                transport.sendto(message)

                # Wait to receive a response BEFORE sending the next message
                try:
                    data, addr = await asyncio.wait_for(protocol.recv(), timeout=2.0)
                    print(f"[Client] Received response: {data.decode()} from {addr}")
                except asyncio.TimeoutError:
                    print("[Client] No response received (timeout)")
                    break

                await asyncio.sleep(0.5)  # Optional small pause

        finally:
            transport.close()

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

        asyncio.run(self.start_client())
