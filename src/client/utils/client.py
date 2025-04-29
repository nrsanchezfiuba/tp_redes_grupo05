import asyncio
import os
from argparse import Namespace

from common.protocol.go_back_n import GoBackN
from common.protocol.protocol import Protocol, mode_mapping, protocol_mapping
from common.protocol.stop_and_wait import StopAndWait
from common.skt.connection_socket import ConnectionSocket
from common.skt.packet import HeaderFlags, Packet


class Client:
    def __init__(self, args: Namespace, selected_mode: str) -> None:
        self.args: Namespace = args
        self.host: str = args.host
        self.port: int = args.port
        self.dst: str = args.dst
        self.name: str = args.name
        self.protocol: str = args.protocol.upper()
        self.verbose: bool = args.verbose
        self.quiet: bool = args.quiet
        self.file_path = os.path.join(self.dst, self.name)

        self.mode = mode_mapping[selected_mode]
        self.protocol_flag = protocol_mapping[self.protocol]

    async def start_client(self) -> None:
        print(f"[Client] Connecting to {self.host}:{self.port}")

        if not self.protocol_flag:
            raise ValueError("Wrong Protocol")

        connection_skt = ConnectionSocket.for_client((self.host, self.port))
        await connection_skt.connect(self.protocol_flag)

        protocol: Protocol = GoBackN(connection_skt, self.verbose)

        if self.protocol == "SW":
            protocol = StopAndWait(connection_skt, self.verbose)
        elif self.protocol == "GBN":
            protocol = GoBackN(connection_skt, self.verbose)

        print(self.protocol, protocol)

        if self.mode.value == HeaderFlags.UPLOAD.value:
            print("[Client] Uploading file...")
            await self.handle_upload(connection_skt, protocol)
        elif self.mode.value == HeaderFlags.DOWNLOAD.value:
            print("[Client] Downloading file...")
            await self.handle_download(connection_skt, protocol)
        else:
            print("[Client] Invalid mode")

    async def _send_mode_and_name(
        self, connection_skt: ConnectionSocket, header_flag: HeaderFlags
    ) -> None:
        mode_packet = Packet(0, 0, b"", header_flag.value | self.protocol_flag.value)
        await connection_skt.send(mode_packet)

        name_packet = Packet(0, 0, self.name.encode(), self.protocol_flag.value)
        await connection_skt.send(name_packet)

    async def handle_download(
        self, connection_skt: ConnectionSocket, protocol: Protocol
    ) -> None:
        await self._send_mode_and_name(connection_skt, HeaderFlags.DOWNLOAD)
        await protocol.recv_file(self.name, self.dst, HeaderFlags.DOWNLOAD.value)
        print(f"[Client] File {self.name} downloaded successfully")

    async def handle_upload(
        self, connection_skt: ConnectionSocket, protocol: Protocol
    ) -> None:
        await self._send_mode_and_name(connection_skt, HeaderFlags.UPLOAD)
        await protocol.send_file(self.name, self.dst, HeaderFlags.UPLOAD.value)
        print(f"[Client] File {self.name} uploaded successfully")

    def run(self) -> None:
        if self.verbose:
            print("Starting client with the following parameters:")
            print(f"Host: {self.host}")
            print(f"Port: {self.port}")
            print(f"Destination path: {self.dst}")
            print(f"Filename: {self.name}")
            print(f"Protocol: {self.protocol}")
            print(f"Mode: {self.mode.value}")
        elif self.quiet:
            pass
        else:
            print("Starting client...")

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
