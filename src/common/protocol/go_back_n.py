import asyncio
from asyncio.tasks import Task
from collections import deque
from typing import Any

from common.config import Config
from common.file_ops.file_manager import FileManager
from common.logger import Logger
from common.protocol.protocol import Protocol
from common.skt.connection_socket import ConnectionSocket
from common.skt.packet import MAX_SEQ_NUM, HeaderFlags, Packet

WINDOW_SIZE: int = 5
RETRANSMIT_TIMEOUT: float = 1.0


class GoBackN(Protocol):
    def __init__(
        self, socket: ConnectionSocket, config: Config, logger: Logger
    ) -> None:
        super().__init__(socket, config, logger)
        self.ack_num = 0
        self.base_seq_num = 0
        self.next_seq_num = 0
        self.unacked_pkts: deque[Packet] = deque()
        self.timer: Task[Any] | None = None

    async def recv_file(self, file_manager: FileManager) -> None:
        try:
            while True:
                packet = await self.socket.recv()
                if self.socket.is_closed():
                    break
                elif packet.get_seq_num() == self.ack_num:
                    self.logger.debug(f"Received valid packet seq={self.ack_num}")
                    file_manager.write_chunk(packet.get_data())
                    ack = Packet(
                        seq_num=0,
                        ack_num=self.ack_num,
                        flags=HeaderFlags.GBN.value
                        | HeaderFlags.ACK.value
                        | self.mode.value,
                    )
                    await self.socket.send(ack)
                    self.ack_num = (self.ack_num + 1) % MAX_SEQ_NUM

        except Exception as e:
            self.logger.error(f"Receive failed: {e}")
            raise

    async def send_file(self, file_manager: FileManager) -> None:
        try:
            while True:
                if (self.next_seq_num - self.base_seq_num) % MAX_SEQ_NUM < WINDOW_SIZE:
                    block = file_manager.read_chunk()
                    if not block:
                        break

                    packet = Packet(
                        seq_num=self.next_seq_num,
                        data=block,
                        flags=HeaderFlags.GBN.value | self.mode.value,
                    )
                    await self.socket.send(packet)

                    self.unacked_pkts.append(packet)

                    # Start timer if first packet in window range
                    if self.base_seq_num == self.next_seq_num:
                        self._start_timer()

                    self.next_seq_num = (self.next_seq_num + 1) % MAX_SEQ_NUM
                else:
                    ack_packet = await self.socket.recv()
                    if ack_packet.is_ack():
                        if ack_packet.get_ack_num() == self.base_seq_num:
                            self.logger.debug(
                                "Received first ACK from the start of the window"
                            )
                            self._stop_timer()
                            self.unacked_pkts.popleft()
                            self.base_seq_num = (self.base_seq_num + 1) % MAX_SEQ_NUM
                        else:
                            self._start_timer()

            self._start_timer()

            while self.unacked_pkts:
                ack_packet = await self.socket.recv()
                if ack_packet.is_ack():
                    if ack_packet.get_ack_num() == self.base_seq_num:
                        self.logger.debug(
                            "Received first ACK from the start of the window"
                        )
                        self._stop_timer()
                        self.unacked_pkts.popleft()
                        self.base_seq_num = (self.base_seq_num + 1) % MAX_SEQ_NUM
                    else:
                        self._start_timer()
        finally:
            # Cleanup tasks
            self.unacked_pkts.clear()
            self._stop_timer()
            await self.socket.disconnect()

    def _start_timer(self) -> None:
        self.timer = asyncio.create_task(self._timeout_handler())

    def _stop_timer(self) -> None:
        if self.timer:
            self.timer.cancel()
            self.timer = None

    async def _timeout_handler(self) -> None:
        try:
            await asyncio.sleep(RETRANSMIT_TIMEOUT)
            self.logger.debug(
                f"[TIMEOUT] Retransmitting window: {self.base_seq_num} to {self.next_seq_num}"
            )

            # Create a local copy of unacked packets to avoid mutation during send
            packets_to_resend = list(self.unacked_pkts)
            for pkt in packets_to_resend:
                self.logger.debug(f"Resending packet seq={pkt.get_seq_num()}")
                await self.socket.send(pkt)

            self._start_timer()  # Restart timer
        except asyncio.CancelledError:
            self.logger.debug("Timer cancelled and reset")
