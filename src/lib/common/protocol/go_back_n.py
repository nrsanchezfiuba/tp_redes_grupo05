import asyncio
from asyncio.tasks import Task
from collections import deque
from typing import Any

from lib.common.config import Config
from lib.common.file_ops.file_manager import FileManager
from lib.common.logger import Logger
from lib.common.protocol.protocol import TIMEOUT_INTERVAL, Protocol
from lib.common.skt.connection_socket import ConnectionSocket
from lib.common.skt.packet import MAX_SEQ_NUM, HeaderFlags, Packet

WINDOW_SIZE: int = 8


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
        await file_manager.open()
        try:
            while True:
                packet = await self.socket.recv()
                if self.socket.is_closed():
                    break
                elif packet.get_seq_num() == self.ack_num:
                    self.logger.debug(f"Received valid packet seq={self.ack_num}")
                    await file_manager.write_chunk(packet.get_data())
                    await self._send_ack(self.ack_num)
                    self.ack_num = (self.ack_num + 1) % MAX_SEQ_NUM
                else:
                    self.logger.debug(
                        f"Received out-of-order packet seq={packet.get_seq_num()}"
                    )
                    await self._send_ack((self.ack_num - 1) % MAX_SEQ_NUM)

        except Exception as e:
            self.logger.error(f"Receive failed: {e}")
            raise
        finally:
            await file_manager.close()

    async def send_file(self, file_manager: FileManager) -> None:
        await file_manager.open()
        try:
            while True:
                if (self.next_seq_num - self.base_seq_num) % MAX_SEQ_NUM < WINDOW_SIZE:
                    block = await file_manager.read_chunk()
                    if not block:
                        break

                    packet = Packet(
                        seq_num=self.next_seq_num,
                        data=block,
                        flags=HeaderFlags.GBN.value | self.mode.value,
                    )
                    await self.socket.send(packet)

                    self.unacked_pkts.append(packet)

                    if self.base_seq_num == self.next_seq_num:
                        self._start_timer()

                    self.next_seq_num = (self.next_seq_num + 1) % MAX_SEQ_NUM
                else:
                    await self._process_acks()

            while self.unacked_pkts:
                await self._process_acks()

        finally:
            await file_manager.close()
            self.unacked_pkts.clear()
            self._stop_timer()
            await self.socket.disconnect()

    async def _process_acks(self) -> None:
        ack_packet = await self.socket.recv()
        if not ack_packet.is_ack():
            return

        ack_num = ack_packet.get_ack_num()

        if self._is_within_window(ack_num):
            while self.unacked_pkts and is_before_or_equal(
                self.unacked_pkts[0].get_seq_num(), ack_num
            ):
                self.unacked_pkts.popleft()

            self.base_seq_num = (ack_num + 1) % MAX_SEQ_NUM

            if self.unacked_pkts:
                self._start_timer()
            else:
                self._stop_timer()

    def _is_within_window(self, seq_num: int) -> bool:
        wrap_around = (self.base_seq_num + WINDOW_SIZE) % MAX_SEQ_NUM
        if self.base_seq_num < wrap_around:
            # If not wrapped around
            return self.base_seq_num <= seq_num < wrap_around
        else:
            # If wrapped around
            return seq_num >= self.base_seq_num or seq_num < wrap_around

    def _start_timer(self) -> None:
        self._stop_timer()  # Cancel existing timer
        self.timer = asyncio.create_task(self._timeout_handler())

    def _stop_timer(self) -> None:
        if self.timer:
            self.timer.cancel()
            self.timer = None

    async def _timeout_handler(self) -> None:
        try:
            await asyncio.sleep(TIMEOUT_INTERVAL)
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

    async def _send_ack(self, ack_num: int) -> None:
        ack = Packet(
            ack_num=ack_num,
            flags=HeaderFlags.GBN.value | HeaderFlags.ACK.value | self.mode.value,
        )
        await self.socket.send(ack)


def is_before_or_equal(seq1: int, seq2: int) -> bool:
    return (seq1 <= seq2 and (seq2 - seq1) < MAX_SEQ_NUM / 2) or (
        seq1 > seq2 and (seq1 - seq2) > MAX_SEQ_NUM / 2
    )
