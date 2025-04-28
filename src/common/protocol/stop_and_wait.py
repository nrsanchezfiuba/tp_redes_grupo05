import asyncio
import os

from common.protocol.protocol import BLOCK_SIZE, Protocol
from common.skt.connection_socket import ConnectionSocket
from common.skt.packet import HeaderFlags, Packet

TIMEOUT_END_CONECTION: float = 5


class StopAndWait(Protocol):
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
            first_packet = await self._receive_first_packet()

            if self._is_file_not_found(first_packet):
                print(f"[ERROR] File '{name}' not found on server")
                return

            await self._process_file_transfer(name, dirpath, first_packet)

        except Exception as e:
            print(f"[ERROR] Receive failed: {e}")
            raise

    async def _send_and_wait_ack(self, packet: Packet, timeout: float = 2.0) -> bool:
        """Send a packet and wait for ACK with retries."""
        seq_num = packet.get_seq_num()
        self._print_debug(f"[DEBUG] Sending packet seq={seq_num}")

        for attempt in range(3):
            if await self._attempt_send_and_wait(packet, seq_num, timeout, attempt):
                return True

        return False

    def save_data(self, data: bytes) -> None:
        if self.current_file is None:
            raise RuntimeError("File not opened for writing.")

        self.current_file.write(data)
        self.current_file.flush()

    async def send_file(self, name: str, dirpath: str, mode: int) -> None:
        try:
            filepath = self._validate_file_path(dirpath, name)
            await self._send_file_contents(filepath, mode)
        except Exception as e:
            print(f"[ERROR] Failed to send file: {e}")
            raise

    async def _receive_first_packet(self) -> Packet:
        """Receive and return the first packet with timeout."""
        return await asyncio.wait_for(self.socket.recv(), timeout=5.0)

    async def _process_file_transfer(
        self, name: str, dirpath: str, first_packet: Packet
    ) -> None:
        """Handle the complete file transfer process."""
        os.makedirs(dirpath, exist_ok=True)
        filepath = os.path.join(dirpath, name)

        with open(filepath, "wb") as file:
            expected_seq = await self._process_first_packet(file, first_packet)
            await self._process_remaining_packets(file, expected_seq)

    async def _process_first_packet(self, file, packet: Packet) -> int:  # type: ignore
        """Process the first packet and return the next expected sequence number."""
        if packet.get_seq_num() == 0:
            self._print_debug("[DEBUG] Received valid packet seq=0")
            file.write(packet.get_data())
            file.flush()
            await self._send_ack(0)
            return 1
        else:
            self._print_debug("[DEBUG] Out-of-order first packet")
            await self._send_ack(1)
            return 0

    async def _process_remaining_packets(self, file, expected_seq: int) -> None:  # type: ignore
        """Process all subsequent packets until transfer completion."""
        while True:
            try:
                packet = await asyncio.wait_for(self.socket.recv(), timeout=5.0)

                if self._is_transfer_complete(packet):
                    self._print_debug("[DEBUG] Transfer complete")
                    break

                expected_seq = await self._process_data_packet(
                    file, packet, expected_seq
                )

            except asyncio.TimeoutError:
                self._print_debug("[DEBUG] No data received, ending transfer")
                break

    async def _process_data_packet(  # type: ignore
        self, file, packet: Packet, expected_seq: int
    ) -> int:
        """Process a data packet and return next expected sequence number."""
        if packet.get_seq_num() == expected_seq:
            self._print_debug(f"[DEBUG] Received valid packet seq={expected_seq}")
            file.write(packet.get_data())
            file.flush()
            await self._send_ack(expected_seq)
            return 1 - expected_seq
        else:
            self._print_debug(
                f"[DEBUG] Out-of-order packet, resending ACK for seq={1 - expected_seq}"
            )
            await self._send_ack(1 - expected_seq)
            return expected_seq

    async def _send_ack(self, seq_num: int) -> None:
        """Send an ACK for the given sequence number."""
        ack = Packet.for_ack(seq_num, 0)
        self._print_debug(f"[DEBUG] Sending ACK for seq={seq_num}")
        await self.socket.send(ack)

    def _validate_file_path(self, dirpath: str, name: str) -> str:
        """Validate and return full file path."""
        filepath = os.path.join(dirpath, name)
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        return filepath

    async def _send_file_contents(self, filepath: str, mode: int) -> None:
        """Send file contents with stop-and-wait protocol."""
        with open(filepath, "rb") as file:
            seq_num = 0
            while True:
                block = file.read(BLOCK_SIZE)
                if not block:
                    await self._send_fin_packet(seq_num)
                    break

                packet = self._create_data_packet(seq_num, block, mode)
                seq_num = await self._send_packet_with_retries(packet, seq_num)

    async def _send_fin_packet(self, seq_num: int) -> None:
        """Send FIN packet to signal end of transmission."""
        self._print_debug("[DEBUG] Sending FIN packet")
        fin_pkt = Packet(
            seq_num,
            0,
            b"",
            HeaderFlags.STOP_WAIT.value | HeaderFlags.FIN.value,
        )
        await self.socket.send(fin_pkt)

    def _create_data_packet(self, seq_num: int, data: bytes, mode: int) -> Packet:
        """Create a data packet with the given sequence number."""
        return Packet(seq_num, 0, data, HeaderFlags.STOP_WAIT.value | mode)

    async def _send_packet_with_retries(self, packet: Packet, current_seq: int) -> int:
        """Send packet with retry logic and return next sequence number."""
        for attempt in range(3):
            try:
                if await self._send_and_wait_ack(packet):
                    return 1 - current_seq  # Toggle sequence number

                self._log_retry_attempt(attempt, current_seq)
                await asyncio.sleep(0.5)

            except Exception as e:
                self._print_debug(f"[DEBUG] Attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    await asyncio.sleep(0.5)

        raise RuntimeError(
            f"Failed to send packet seq_num={current_seq} after 3 attempts"
        )

    def _log_retry_attempt(self, attempt: int, seq_num: int) -> None:
        """Log retry attempts."""
        if attempt < 2:
            self._print_debug(
                f"[DEBUG] Retrying seq_num={seq_num} (attempt {attempt + 2})"
            )

    async def _attempt_send_and_wait(
        self, packet: Packet, seq_num: int, timeout: float, attempt: int
    ) -> bool:
        """Single attempt to send packet and wait for ACK."""
        try:
            await self.socket.send(packet)
            self._print_debug(f"[DEBUG] Waiting for ACK (attempt {attempt + 1})")

            while True:
                ack_packet = await asyncio.wait_for(self.socket.recv(), timeout)
                return self._process_ack_packet(ack_packet, seq_num)

        except asyncio.TimeoutError:
            self._print_debug("[DEBUG] Timeout waiting for ACK, retrying...")
            return False

    def _process_ack_packet(self, ack_packet: Packet, expected_seq: int) -> bool:
        """Process received ACK packet and return True if valid."""
        if ack_packet.is_ack():
            self._print_debug(f"[DEBUG] Received valid ACK for seq={expected_seq}")
            return True
        else:
            self._print_debug("[DEBUG] Received non-ACK packet, ignoring")
            return False

    def _is_transfer_complete(self, packet: Packet) -> bool:
        """Check if packet indicates transfer completion."""
        return packet.is_fin()

    def _is_file_not_found(self, packet: Packet) -> bool:
        """Check if packet indicates file not found."""
        return packet.is_fin()
