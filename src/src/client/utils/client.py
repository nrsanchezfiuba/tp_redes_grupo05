import asyncio
import os
from argparse import Namespace

from common.config import Config
from common.protocol.go_back_n import GoBackN
from common.protocol.protocol import Protocol, mode_mapping, protocol_mapping
from common.protocol.stop_and_wait import StopAndWait
from common.skt.connection_socket import ConnectionSocket
from common.skt.packet import HeaderFlags, Packet


class Client:
    def __init__(self, args: Namespace, selected_mode: str) -> None:
        self.config = Config(args)
        self.mode = mode_mapping[selected_mode]

    async def start_client(self) -> None:
        print(f"[Client] Connecting to {self.config.host}:{self.config.port}")

        connection_skt = ConnectionSocket.for_client(
            (self.config.host, self.config.port)
        )
        await connection_skt.connect(self.config.protocol_type)

        protocol: Protocol = self._init_protocol_for_connection(connection_skt)
        await protocol.initiate_transaction(self.config.name, self.mode)

    def run(self) -> None:
        if self.config.verbose:
            print("Starting client with the following parameters:")
            print(f"Host: {self.config.host}")
            print(f"Port: {self.config.port}")
            print(f"Destination path: {self.config.dst}")
            print(f"Filename: {self.config.name}")
            print(f"Protocol: {self.config.protocol_type}")
            print(f"Mode: {self.mode}")
        elif self.config.quiet:
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

    def _init_protocol_for_connection(self, conn: ConnectionSocket) -> Protocol:
        match self.config.protocol_type:
            case HeaderFlags.STOP_WAIT:
                return StopAndWait(conn, self.config)
            case HeaderFlags.GBN:
                return GoBackN(conn, self.config)
            case _:
                raise ValueError("Invalid protocol type")
