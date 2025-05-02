import asyncio

from common.config import Config
from common.file_ops.file_manager import FileManager
from common.logger import Logger
from common.protocol.protocol import TIMEOUT_END_CONECTION, Protocol
from common.skt.connection_socket import ConnectionSocket
from common.skt.packet import HeaderFlags, Packet


class StopAndWait(Protocol):
    def __init__(self, socket: ConnectionSocket, config: Config, logger: Logger):
        super().__init__(socket, config, logger)
        self.ack_num = 0
        self.seq_num = 0

    async def recv_file(self, file_manager: FileManager) -> None:
        while True:
            try:
                packet = await asyncio.wait_for(
                    self.socket.recv(), timeout=TIMEOUT_END_CONECTION
                )
                if self.socket.is_closed():
                    break

                if packet.get_seq_num() == self.ack_num:
                    self.logger.debug(f"Received valid packet seq={self.ack_num}")
                    file_manager.write_chunk(packet.get_data())
                    ack = Packet(
                        ack_num=self.ack_num,
                        flags=HeaderFlags.SW.value
                        | HeaderFlags.ACK.value
                        | self.mode.value,
                    )
                    await self.socket.send(ack)
                    self.ack_num = 1 - self.ack_num
                else:
                    ack = Packet(
                        ack_num=self.ack_num,
                        flags=HeaderFlags.SW.value
                        | HeaderFlags.ACK.value
                        | self.mode.value,
                    )
                    await self.socket.send(ack)
            except TimeoutError:
                continue

    async def send_file(self, file_manager: FileManager) -> None:
        while True:
            block = file_manager.read_chunk()
            if not block:
                await self.socket.disconnect()
                break

            packet = Packet(
                seq_num=self.seq_num,
                data=block,
                flags=HeaderFlags.SW.value | self.mode.value,
            )
            for attempt in range(3):
                try:
                    if await self._send_and_wait_ack(packet):
                        self.seq_num = 1 - self.seq_num
                        break

                    await asyncio.sleep(0.5)
                except TimeoutError as e:
                    self.logger.debug(f"Attempt {attempt + 1} failed: {e}")
                    await asyncio.sleep(0.5)

    async def _send_and_wait_ack(
        self, packet: Packet, timeout: float = TIMEOUT_END_CONECTION
    ) -> bool:
        seq_num = packet.get_seq_num()
        self.logger.debug(f"Sending packet seq={seq_num}")

        await self.socket.send(packet)
        ack_packet = await asyncio.wait_for(self.socket.recv(), timeout)
        return ack_packet.is_ack()
