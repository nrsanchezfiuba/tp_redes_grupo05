import asyncio

from common.protocol.protocol import BLOCK_SIZE, Protocol
from common.skt.connection_socket import ConnectionSocket
from common.skt.packet import HeaderFlags, Packet

TIMEOUT_END_CONECTION: float = 5


class StopAndWait(Protocol):
    def __init__(self, socket: ConnectionSocket):
        super().__init__(socket)

    async def recv_file(self, name: str, dirpath: str, mode: int) -> None:
        print(f"[RecvFile]: Receiving file {name} to {dirpath}")
        try:
            while True:
                recv_pkt = await asyncio.wait_for(
                    self.socket.recv(), TIMEOUT_END_CONECTION
                )

                if not recv_pkt.header_data.length:
                    continue

                print("Got data, sending ack")
                await self.socket.send(Packet.for_ack(0, 0))

                self.save_data(recv_pkt.get_data(), dirpath)
        except asyncio.TimeoutError:
            print("TIMEOUT in SW.recv_file")
            return
        except Exception as e:
            raise RuntimeError(f"Unexpected error: {e}")

    async def send_file(self, name: str, filepath: str, mode: int) -> None:
        try:
            with open(
                "./storage/data.txt",
                "rb",
            ) as file:
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
                            break
                        retry_count += 1

        except FileNotFoundError:
            raise FileNotFoundError(f"El archivo '{filepath}' no existe.")
        except Exception as e:
            raise RuntimeError(f"Error inesperado: {e}")

    async def _send_and_wait_ack(self, packet: Packet, timeout: float = 1.0) -> bool:
        print(packet)
        await self.socket.send(packet)

        received_ack = False
        try:
            recv_pkt = await asyncio.wait_for(self.socket.recv(), timeout=timeout)
            received_ack = recv_pkt.is_ack()
        except asyncio.TimeoutError:
            print(" Timeout: No ACK received.")
        except Exception as e:
            raise RuntimeError(f"Unexpected error: {e}")

        return received_ack
