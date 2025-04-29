import os

from common.protocol.protocol import BLOCK_SIZE, Protocol
from common.skt.connection_socket import ConnectionSocket
from common.skt.packet import MAX_SEQ_NUM, HeaderFlags, Packet

TIMEOUT_END_CONECTION: float = 5
WINDOW_SIZE: int = 5


class GoBackN(Protocol):
    def __init__(self, socket: ConnectionSocket, verbose: bool = False):
        super().__init__(socket)
        self.received_data = bytearray()
        self.current_file = None
        self.expected_seq_num = 0
        self.verbose = verbose

    def _print_debug(self, message: str) -> None:
        if self.verbose:
            print(message)

    async def recv_file(self, name: str, dirpath: str, mode: int) -> None:
        try:
            filepath = os.path.join(dirpath, name)

            with open(filepath, "wb") as file:
                while True:
                    packet = await self.socket.recv()
                    if packet.get_seq_num() == self.expected_seq_num:
                        self._print_debug(
                            f"[DEBUG] Received valid packet seq={self.expected_seq_num}"
                        )
                        file.write(packet.get_data())
                        file.flush()
                        await self._send_ack(0, self.expected_seq_num)
                        self.expected_seq_num += 1
                        self.expected_seq_num %= MAX_SEQ_NUM
                    elif packet.is_fin():
                        break

        except Exception as e:
            print(f"[ERROR] Receive failed: {e}")
            raise

    async def send_file(self, name: str, dirpath: str, mode: int) -> None:
        try:
            filepath = self._validate_file_path(dirpath, name)
            await self._send_file_contents(filepath, mode)
        except Exception as e:
            print(f"[ERROR] Failed to send file: {e}")
            raise

    def save_data(self, data: bytes) -> None:
        if self.current_file is None:
            raise RuntimeError("File not opened for writing.")

        self.current_file.write(data)
        self.current_file.flush()

    async def _send_file_contents(self, filepath: str, mode: int) -> None:
        """Send file contents with stop-and-wait protocol."""
        with open(filepath, "rb") as file:
            self.base = 0
            self.next_seq_num = 0

            while True:
                if (self.next_seq_num - self.base) % MAX_SEQ_NUM < WINDOW_SIZE:
                    block = file.read(BLOCK_SIZE)
                    if not block:
                        break

                    packet = self._create_data_packet(self.next_seq_num, 0, block, mode)
                    await self.socket.send(packet)

                    self.next_seq_num += 1
                    self.next_seq_num %= MAX_SEQ_NUM
                else:
                    ack_packet = await self.socket.recv()
                    if self._process_ack_packet(ack_packet, self.base):
                        self.base += 1
                        self.base %= MAX_SEQ_NUM

            await self._send_fin_packet(0)

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

    def _process_ack_packet(self, ack_packet: Packet, expected_seq: int) -> bool:
        """Process received ACK packet and return True if valid."""
        if ack_packet.is_ack():
            self._print_debug(f"[DEBUG] Received valid ACK for seq={expected_seq}")
            return True
        else:
            self._print_debug("[DEBUG] Received non-ACK packet, ignoring")
            return False

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
