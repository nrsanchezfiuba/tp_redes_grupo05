import asyncio

from common.packet import HeaderFlags, Packet
from common.protocol.protocol import BLOCK_SIZE, Protocol
from common.udp_socket import UDPSocket

TIMEOUT_END_CONECTION: float = 5


class StopAndWait(Protocol):
    def __init__(self, socket: UDPSocket):
        super().__init__(socket)

    async def recv_file(self, name: str, filepath: str, mode: int) -> None:
        try:
            while True:
                response, sender = await asyncio.wait_for(
                    self.socket.recv_all(), TIMEOUT_END_CONECTION
                )
                recv_packet = Packet.from_bytes(response)

                while not recv_packet.header_data.length:
                    response, sender = await asyncio.wait_for(
                        self.socket.recv_all(), TIMEOUT_END_CONECTION
                    )
                    recv_packet = Packet.from_bytes(response)

                self.save_data(response, filepath)
                await self.socket.send_all(Packet.for_ack(0, 0).to_bytes(), ("0", 0))
        except asyncio.TimeoutError:
            # TODO vervose mode end conection
            return
        except Exception as e:
            raise RuntimeError(f"Unexpected error: {e}")

    async def send_file(self, name: str, filepath: str, mode: int) -> None:
        try:
            with open(filepath, "rb") as file:
                seq_num: int = 0
                ack_num: int = 0
                max_retries: int = 3
                retry_count: int
                while True:
                    retry_count = 0
                    block = file.read(BLOCK_SIZE)
                    if not block:
                        break

                    packet = Packet(
                        seq_num, ack_num, block, HeaderFlags.STOP_WAIT.value | mode
                    )

                while retry_count < max_retries:
                    if await self.send_and_wait_ack(packet, timeout=1.0):
                        break  # ACK recibido
                    retry_count += 1

        except FileNotFoundError:
            raise FileNotFoundError(f"El archivo '{filepath}' no existe.")
        except Exception as e:
            raise RuntimeError(f"Error inesperado: {e}")

    async def send_and_wait_ack(self, packet: Packet, timeout: float = 1.0) -> bool:
        await self.socket.send_all(packet.to_bytes(), ("0", 0))

        try:
            response, sender = await asyncio.wait_for(
                self.socket.recv_all(), timeout=timeout
            )
            recv_packet: Packet = Packet.from_bytes(response)

            # If not ACK, keep waiting (with timeout)
            while not recv_packet.is_ack():
                response, sender = await asyncio.wait_for(
                    self.socket.recv_all(), timeout=timeout
                )
                recv_packet = Packet.from_bytes(response)

            return True  # ACK received

        except asyncio.TimeoutError:
            print(" Timeout: No ACK received.")  # TODO for vervose
            return False
        except Exception as e:
            raise RuntimeError(f"Unexpected error: {e}")
