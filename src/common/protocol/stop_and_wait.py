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
            os.makedirs(dirpath, exist_ok=True)
            filepath = os.path.join(dirpath, name)

            with open(filepath, "wb") as file:
                expected_seq = 0

                while True:
                    try:
                        packet = await asyncio.wait_for(self.socket.recv(), timeout=5.0)

                        if packet.is_fin():
                            self._print_debug("[DEBUG] Transfer complete")
                            break

                        if packet.get_seq_num() == expected_seq:
                            self._print_debug(
                                f"[DEBUG] Received valid packet seq={expected_seq}"
                            )
                            file.write(packet.get_data())
                            file.flush()
                            ack = Packet.for_ack(expected_seq, 0)
                            self._print_debug(
                                f"[DEBUG] Sending ACK for seq={expected_seq}"
                            )
                            await self.socket.send(ack)
                            expected_seq = 1 - expected_seq
                        else:
                            self._print_debug(
                                f"[DEBUG] Out-of-order packet, resending ACK for seq={1-expected_seq}"
                            )
                            await self.socket.send(Packet.for_ack(1 - expected_seq, 0))

                    except asyncio.TimeoutError:
                        self._print_debug("[DEBUG] No data received, ending transfer")
                        break
        except Exception as e:
            print(f"[ERROR] Receive failed: {e}")
            raise

    def save_data(self, data: bytes) -> None:
        """Save received data on file."""
        if self.current_file is None:
            raise RuntimeError("File not opened for writing.")

        self.current_file.write(data)
        self.current_file.flush()

    async def send_file(self, name: str, dirpath: str, mode: int) -> None:
        try:
            filepath = os.path.join(dirpath, name)

            if not os.path.isfile(filepath):
                raise FileNotFoundError(f"File not found: {filepath}")

            with open(filepath, "rb") as file:
                seq_num = 0
                while True:
                    block = file.read(BLOCK_SIZE)
                    if not block:
                        self._print_debug("[DEBUG] Sending FIN packet")
                        fin_pkt = Packet(
                            seq_num,
                            0,
                            b"",
                            HeaderFlags.STOP_WAIT.value | HeaderFlags.FIN.value,
                        )
                        await self.socket.send(fin_pkt)
                        break

                    packet = Packet(
                        seq_num, 0, block, HeaderFlags.STOP_WAIT.value | mode
                    )

                    retry_count = 0
                    while retry_count < 3:
                        try:
                            if await self._send_and_wait_ack(packet):
                                seq_num = 1 - seq_num
                                break
                        except Exception as e:
                            self._print_debug(
                                f"[DEBUG] Attempt {retry_count+1} failed: {e}"
                            )

                        retry_count += 1
                        if retry_count < 3:
                            self._print_debug(
                                f"[DEBUG] Retrying seq_num={seq_num} (attempt {retry_count+1})"
                            )
                            await asyncio.sleep(0.5)
                    else:
                        raise RuntimeError(
                            f"Failed to send packet seq_num={seq_num} after 3 attempts"
                        )

        except Exception as e:
            print(f"[ERROR] Failed to send file: {e}")
            raise

    async def _send_and_wait_ack(self, packet: Packet, timeout: float = 2.0) -> bool:
        seq_num = packet.get_seq_num()
        self._print_debug(f"[DEBUG] Sending packet seq={seq_num}")

        for attempt in range(3):
            try:
                await self.socket.send(packet)
                self._print_debug(f"[DEBUG] Waiting for ACK (attempt {attempt+1})")

                while True:
                    ack_packet = await asyncio.wait_for(self.socket.recv(), timeout)

                    if ack_packet.is_ack():
                        self._print_debug(
                            f"[DEBUG] Received valid ACK for seq={seq_num}"
                        )
                        return True
                    else:
                        self._print_debug("[DEBUG] Received non-ACK packet, ignoring")

            except asyncio.TimeoutError:
                self._print_debug("[DEBUG] Timeout waiting for ACK, retrying...")
                continue
        return False
