import asyncio

from lib.common.config import Config
from lib.common.file_ops.file_manager import FileManager
from lib.common.logger import Logger
from lib.common.protocol.protocol import (
    RETRANSMISSION_RETRIES,
    TIMEOUT_INTERVAL,
    Protocol,
)
from lib.common.skt.connection_socket import ConnectionSocket
from lib.common.skt.packet import HeaderFlags, Packet


class StopAndWait(Protocol):
    def __init__(self, socket: ConnectionSocket, config: Config, logger: Logger):
        super().__init__(socket, config, logger)
        self.ack_num = 0
        self.seq_num = 0

    async def recv_file(self, file_manager: FileManager) -> None:
        await file_manager.open()
        while True:
            try:
                packet = await asyncio.wait_for(
                    self.socket.recv(), timeout=TIMEOUT_INTERVAL
                )
                if self.socket.is_closed():
                    break

                if packet.get_seq_num() == self.ack_num:
                    self.logger.debug(f"Received valid packet seq={self.ack_num}")
                    await file_manager.write_chunk(packet.get_data())
                    self.ack_num = 1 - self.ack_num

                await self._send_ack()
            except TimeoutError:
                continue
        await file_manager.close()

    async def send_file(self, file_manager: FileManager) -> None:
        await file_manager.open()
        while True:
            block = await file_manager.read_chunk()
            if not block:
                await self.socket.disconnect()
                break

            for attempt in range(RETRANSMISSION_RETRIES):
                try:
                    await self._send_data(block)
                    self.seq_num = 1 - self.seq_num
                    break
                except TimeoutError as e:
                    self.logger.debug(f"Attempt {attempt + 1} failed: {e}")
                    await asyncio.sleep(TIMEOUT_INTERVAL)
            else:
                self.logger.error("Failed to receive ACK for packet")
                await self.socket.disconnect()
                break
        await file_manager.close()

    async def _send_ack(self) -> None:
        ack = Packet(
            ack_num=self.ack_num,
            flags=HeaderFlags.SW.value | HeaderFlags.ACK.value | self.mode.value,
        )
        await self.socket.send(ack)

    async def _send_data(self, data: bytes) -> None:
        self.logger.debug(f"Sending packet seq={self.seq_num}")
        packet = Packet(
            seq_num=self.seq_num,
            data=data,
            flags=HeaderFlags.SW.value | self.mode.value,
        )
        await self.socket.send(packet)
        ack_packet = await asyncio.wait_for(
            self.socket.recv(), timeout=TIMEOUT_INTERVAL
        )
        if not ack_packet.is_ack():
            raise TimeoutError("Failed to receive ACK for packet")
