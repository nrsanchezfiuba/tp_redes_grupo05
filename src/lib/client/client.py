import asyncio
from argparse import Namespace

from lib.common.config import Config
from lib.common.logger import Logger
from lib.common.protocol.protocol import Protocol
from lib.common.skt.connection_socket import ConnectionSocket


class Client:
    def __init__(self, args: Namespace, selected_mode: str) -> None:
        self.config = Config(args, client=True, client_mode=selected_mode)
        self.logger: Logger = Logger(
            self.config.verbose, self.config.quiet, self.config.log_file
        )

    def run(self) -> None:
        self.logger.debug(
            "Starting client with the following parameters:\n"
            f"Host: {self.config.host}\n"
            f"Port: {self.config.port}\n"
            f"Destination path: {self.config.client_dst}\n"
            f"Filename: {self.config.client_filename}\n"
            f"Protocol: {self.config.protocol_type}\n"
            f"Mode: {self.config.client_mode}"
        )
        self.logger.info("Starting client...")

        loop = asyncio.get_event_loop()

        try:
            loop.run_until_complete(self.start_client())
        except (KeyboardInterrupt, TimeoutError) as e:
            if str(e) != "":
                self.logger.error(str(e))
            self.logger.info("[Client] Stopping client...")

            tasks = [t for t in asyncio.all_tasks(loop=loop) if not t.done()]
            for task in tasks:
                task.cancel()

            loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        finally:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()

    async def start_client(self) -> None:
        if not self.config.quiet:
            self.logger.info(
                f"[Client] Connecting to {self.config.host}:{self.config.port}"
            )

        connection_skt = ConnectionSocket.for_client(
            (self.config.host, self.config.port), self.config.protocol_type, self.logger
        )
        await connection_skt.connect()

        protocol = Protocol.from_connection(connection_skt, self.config, self.logger)
        await protocol.initiate_transaction()
