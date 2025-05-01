import asyncio
import os
from collections import deque

from common.protocol.protocol import BLOCK_SIZE, Protocol
from common.skt.connection_socket import ConnectionSocket
from common.skt.packet import MAX_SEQ_NUM, HeaderFlags, Packet
from common.file_ops.file_manager import FileManager, FileOperation
from server.config import ServerConfig

TIMEOUT_END_CONECTION: float = 5
WINDOW_SIZE: int = 5
RETRANSMIT_TIMEOUT: float = 0.5


class GoBackN(Protocol):
    def __init__(self, socket: ConnectionSocket, config: ServerConfig):
        super().__init__(socket)
        self.received_data = bytearray()
        self.current_file = None
        self.expected_seq_num = 0
        self.config = config
        self.unacked_pkts: deque[Packet] = deque()
        self.timer = None

    async def handle_connection(self) -> None:
        file_name_pkt = await self.socket.recv()
        try:
            match file_name_pkt.get_mode():
                case HeaderFlags.UPLOAD:
                    file_name = file_name_pkt.get_data().decode().strip()
                    file_manager = FileManager(
                        self.config.dirpath, file_name, FileOperation.WRITE
                    )
                    self.current_file = file_manager.file
                    await self.recv_file(file_manager, 1)
                case HeaderFlags.DOWNLOAD:
                    file_name = file_name_pkt.get_data().decode().strip()
                    file_manager = FileManager(
                        self.config.dirpath, file_name, FileOperation.READ
                    )
                    self.current_file = file_manager.file
                    await self.send_file(file_manager, 0)
                case _:
                    raise ValueError("Invalid mode in packet")
        except FileNotFoundError:
            print(
                f"[ERROR] File not found: {file_name_pkt.get_data().decode().strip()}"
            )
            fin_pkt = Packet(
                HeaderFlags.GBN.value | HeaderFlags.FIN.value,
            )
            await self.socket.send(fin_pkt)

    def _print_debug(self, message: str) -> None:
        if self.config.verbose:
            print(message)

    async def recv_file(self, file_manager: FileManager, mode: int) -> None:
        try:
            while True:
                packet = await self.socket.recv()
                if packet.get_seq_num() == self.expected_seq_num:
                    self._print_debug(
                        f"[DEBUG] Received valid packet seq={self.expected_seq_num}"
                    )
                    file_manager.write_file(packet.get_data())
                    await self._send_ack(0, self.expected_seq_num)
                    self.expected_seq_num += 1
                    self.expected_seq_num %= MAX_SEQ_NUM
                elif packet.is_fin():
                    break

        except Exception as e:
            print(f"[ERROR] Receive failed: {e}")
            raise

    async def send_file(self, file_manager: FileManager, mode: int) -> None:
        try:
            await self._send_file_contents(file_manager, mode)
        except Exception as e:
            print(f"[ERROR] Failed to send file: {e}")
            raise

    def save_data(self, data: bytes) -> None:
        if self.current_file is None:
            raise RuntimeError("File not opened for writing.")

        self.current_file.write(data)
        self.current_file.flush()

    async def _send_file_contents(self, file_manager: FileManager, mode: int) -> None:
        """Send file contents with stop-and-wait protocol."""
        self.base = 0
        self.next_seq_num = 0
        try:
            while True:
                if (self.next_seq_num - self.base) % MAX_SEQ_NUM < WINDOW_SIZE:
                    block = file_manager.read_file(BLOCK_SIZE)
                    if not block:
                        break

                    packet = self._create_data_packet(self.next_seq_num, 0, block, mode)
                    await self.socket.send(packet)

                    self.unacked_pkts.append(packet)

                    # Start timer if first packet in window range
                    if self.base == self.next_seq_num:
                        self._start_timer()

                    self.next_seq_num = (self.next_seq_num + 1) % MAX_SEQ_NUM
                else:
                    ack_packet = await self.socket.recv()
                    if ack_packet.is_ack():
                        if ack_packet.get_ack_num() == self.base:
                            self._print_debug(
                                "[DEBUG] Received first ACK from the start of the window"
                            )
                            self._stop_timer()
                            self.unacked_pkts.popleft()
                            self.base = (self.base + 1) % MAX_SEQ_NUM
                        else:
                            self._start_timer()

            self._start_timer()

            while self.unacked_pkts:
                ack_packet = await self.socket.recv()
                if ack_packet.is_ack():
                    if ack_packet.get_ack_num() == self.base:
                        self._print_debug(
                            "[DEBUG] Received first ACK from the start of the window"
                        )
                        self._stop_timer()
                        self.unacked_pkts.popleft()
                        self.base = (self.base + 1) % MAX_SEQ_NUM
                    else:
                        self._start_timer()

            self._stop_timer()

            await self._send_fin_packet(0)
        finally:
            # Cleanup tasks
            self.unacked_pkts.clear()
            self._stop_timer()

    async def _send_fin_packet(self, seq_num: int) -> None:
        """Send FIN packet to signal end of transmission."""
        self._print_debug("[DEBUG] Sending FIN packet")
        fin_pkt = Packet(
            seq_num,
            0,
            b"",
            HeaderFlags.GBN.value | HeaderFlags.FIN.value,
        )
        await self.socket.send(fin_pkt)

    def _create_data_packet(
        self, seq_num: int, ack_num: int, data: bytes, mode: int
    ) -> Packet:
        """Create a data packet with the given sequence number."""
        return Packet(seq_num, ack_num, data, HeaderFlags.GBN.value | mode)

    def _validate_file_path(self, dirpath: str, name: str) -> str:
        """Validate and return full file path."""
        filepath = os.path.join(dirpath, name)
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        return filepath

    async def _send_ack(self, seq_num: int, ack_num: int) -> None:
        """Send an ACK for the given sequence number."""
        ack = Packet.for_ack(seq_num, ack_num, HeaderFlags.GBN)
        self._print_debug(f"[DEBUG] Sending ACK for seq={seq_num}")
        await self.socket.send(ack)

    def _is_transfer_complete(self, packet: Packet) -> bool:
        """Check if packet indicates transfer completion('fin' flag is sent) ."""
        return packet.is_fin()

    def _is_file_not_found(self, packet: Packet) -> bool:
        """Check if packet indicates file not found('fin' flag is sent)."""
        return packet.is_fin()

    def _start_timer(self) -> None:
        """Start or restart the timer"""
        self.timer = asyncio.create_task(self._timeout_handler())  # type: ignore

    def _stop_timer(self) -> None:
        """Stop the timer"""
        if self.timer:
            self.timer.cancel()
            self.timer = None

    async def _timeout_handler(self) -> None:
        """Handle timeout by retransmitting all unacked packets"""
        try:
            await asyncio.sleep(RETRANSMIT_TIMEOUT)
            self._print_debug(
                f"[TIMEOUT] Retransmitting window: {self.base} to {self.next_seq_num}"
            )

            # Create a local copy of unacked packets to avoid mutation during send
            packets_to_resend = list(self.unacked_pkts)
            for pkt in packets_to_resend:
                self._print_debug(f"[DEBUG] Resending packet seq={pkt.get_seq_num()}")
                await self.socket.send(pkt)

            self._start_timer()  # Restart timer
        except asyncio.CancelledError:
            self._print_debug("[DEBUG] Timer cancelled and reset")
