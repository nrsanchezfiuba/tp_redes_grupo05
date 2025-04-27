import asyncio

from common.protocol.protocol import BLOCK_SIZE, Protocol
from common.socket.connection_socket import ConnectionSocket
from common.socket.packet import HeaderFlags, Packet

TIMEOUT_END_CONECTION: float = 5


class StopAndWait(Protocol):
    def __init__(self, socket: ConnectionSocket):
        super().__init__(socket)

    async def recv_file(self, name: str, filepath: str, mode: int) -> None:
        try:
            while True:
                recv_pkt = await asyncio.wait_for(
                    self.socket.recv(), TIMEOUT_END_CONECTION
                )

                while not recv_pkt.header_data.length:
                    recv_pkt = await asyncio.wait_for(
                        self.socket.recv(), TIMEOUT_END_CONECTION
                    )

                self.save_data(recv_pkt.get_data(), filepath)
                await self.socket.send(Packet.for_ack(0, 0))
        except asyncio.TimeoutError:
            # TODO vervose mode end conection
            return
        except Exception as e:
            raise RuntimeError(f"Unexpected error: {e}")

    async def send_file(self, name: str, filepath: str, mode: int) -> None:
        try:

            print("hola")

            pkt = await self.socket.recv()

            print("hola2")

            print(f"[SendFile]: Received packet {pkt}")
            while not pkt.is_syn() and not pkt.is_ack():
                pkt = await self.socket.recv()

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
                    if await self._send_and_wait_ack(packet, timeout=1.0):
                        break  # ACK recibido
                    retry_count += 1

        except FileNotFoundError:
            raise FileNotFoundError(f"El archivo '{filepath}' no existe.")
        except Exception as e:
            raise RuntimeError(f"Error inesperado: {e}")

    async def _send_and_wait_ack(self, packet: Packet, timeout: float = 1.0) -> bool:
        await self.socket.send(packet)

        try:
            recv_pkt = await asyncio.wait_for(self.socket.recv(), timeout=timeout)

            # If not ACK, keep waiting (with timeout)
            while not recv_pkt.is_ack():
                recv_pkt = await asyncio.wait_for(self.socket.recv(), timeout=timeout)

            return True  # ACK received

        except asyncio.TimeoutError:
            print(" Timeout: No ACK received.")  # TODO for vervose
            return False
        except Exception as e:
            raise RuntimeError(f"Unexpected error: {e}")
