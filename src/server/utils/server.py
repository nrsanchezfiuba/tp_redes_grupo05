import asyncio
import os
from argparse import Namespace

from common.flow_manager import FlowManager
from common.skt.acceptor_socket import AcceptorSocket
from common.skt.packet import HeaderFlags


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

        header_flag = HeaderFlags.STOP_WAIT

        if self.protocol == "SW":
            header_flag = HeaderFlags.STOP_WAIT
        elif self.protocol == "GBN":
            header_flag = HeaderFlags.GBN
        else:
            raise ValueError("I dont have this protocol. Suck my dick")

        self.flow_manager = FlowManager()
        self.acceptor_skt = AcceptorSocket(header_flag, self.flow_manager)

    async def start_server(self) -> None:
        self.acceptor_skt
        # await self.socket.init_connection(self.host, self.port)
        # if not self.quiet:
        #     print(
        #         f"Server listening on {self.host}:{self.port} using {self.protocol} protocol"
        #     )

        # while True:
        #     data, addr = await self.socket.recv_all()

        #     if self.verbose:
        #         print(f"Received {len(data)} bytes from {addr}")

        #     client_data = Packet.from_bytes(data)
        #     print(repr(client_data))
        #     length = client_data.header_data.length

        #     response = Packet(
        #         seq_num=length,
        #         ack_num=length + client_data.get_seq_num(),
        #         data=b"ACK",
        #         flags=HeaderFlags.ACK.value,
        #     )

        #     self.socket.send_all(response.to_bytes(), addr)

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

            tasks = [t for t in asyncio.all_tasks(loop=loop) if not t.done()]
            for task in tasks:
                task.cancel()

            loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        finally:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()
