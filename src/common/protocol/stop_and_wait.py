from common.packet import HeaderFlags, Packet
from common.protocol.protocol import BLOCK_SIZE, Protocol
from common.udp_socket import UDPSocket


class StopAndWait(Protocol):
    def __init__(self, socket: UDPSocket):
        super().__init__(socket)

    async def recv_file(self, name: str, filepath: str, mode: int) -> None:

        while True:
            response, sender = await self.socket.recv_all()
            recv_packet = Packet.from_bytes(response)

            while not recv_packet.header_data.length:
                response, sender = await self.socket.recv_all()
                recv_packet = Packet.from_bytes(response)

            self.save_data(response, filepath)
            await self.socket.send_all(Packet.for_ack(0, 0).to_bytes(), ("0", 0))

    async def send_file(self, name: str, filepath: str, mode: int) -> None:
        try:
            with open(filepath, "rb") as file:
                seq_num: int = 0
                ack_num: int = 0
                while True:

                    block = file.read(BLOCK_SIZE)
                    if not block:
                        break

                    packet = Packet(
                        seq_num, ack_num, block, HeaderFlags.STOP_WAIT.value | mode
                    )
                    await self.socket.send_all(packet.to_bytes(), ("0", 0))

                    [response, sender] = await self.socket.recv_all()
                    recv_packet = Packet.from_bytes(response)
                    while not recv_packet.is_ack():
                        response, sender = await self.socket.recv_all()
                        recv_packet = Packet.from_bytes(response)

        except FileNotFoundError:
            raise FileNotFoundError(f"El archivo '{filepath}' no existe.")
        except Exception as e:
            raise RuntimeError(f"Error inesperado: {e}")
