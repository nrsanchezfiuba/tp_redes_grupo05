import asyncio
from argparse import Namespace
from asyncio.queues import Queue

from lib.common.config import Config
from lib.common.flow_manager import FlowManager
from lib.common.logger import Logger
from lib.common.protocol.protocol import Protocol
from lib.common.skt.acceptor_socket import AcceptorSocket
from lib.common.skt.connection_socket import ConnectionSocket


class Server:
    def __init__(self, args: Namespace) -> None:
        self.config = Config(args, server=True)
        self.logger = Logger(
            self.config.verbose, self.config.quiet, self.config.log_file
        )
        self.flow_manager = FlowManager()
        self.acceptor_skt = AcceptorSocket(
            self.config.protocol_type, self.flow_manager, self.logger
        )

    def run(self) -> None:
        self.logger.debug(
            "[Server] Starting server with the following parameters:\n"
            f"[Server] Host: {self.config.host}\n"
            f"[Server] Port: {self.config.port}\n"
            f"[Server] Storage folder dir path: {self.config.server_dirpath}\n"
            f"[Server] Protocol: {self.config.protocol_type}"
        )
        self.logger.info("[Server] Starting server...")

        loop = asyncio.get_event_loop()

        try:
            loop.run_until_complete(self.start_server())
        except KeyboardInterrupt:
            self.logger.info("\n[Server] Stopping server...")

            tasks = [t for t in asyncio.all_tasks(loop=loop) if not t.done()]
            for task in tasks:
                task.cancel()

            loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        finally:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()

    async def start_server(self) -> None:
        self.acceptor_skt.bind(self.config.host, self.config.port)
        incoming_connections: Queue[ConnectionSocket] = asyncio.Queue()

        async def acceptor_callback() -> None:
            while True:
                connection_skt = await self.acceptor_skt.accept()
                await incoming_connections.put(connection_skt)

        async def handle_connection() -> None:
            while True:
                connection_skt = await incoming_connections.get()

                protocol = Protocol.from_connection(
                    connection_skt, self.config, self.logger
                )
                asyncio.create_task(protocol.handle_connection())

        acceptor_task = asyncio.create_task(acceptor_callback())
        handle_task = asyncio.create_task(handle_connection())

        await asyncio.gather(acceptor_task, handle_task)
