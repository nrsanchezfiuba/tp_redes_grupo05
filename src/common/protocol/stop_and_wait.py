from common.packet import Packet
from common.protocol.protocol import BLOCK_SIZE, Protocol


class StopAndWait(Protocol):
    def __init__(self, socket):  # type: ignore
        super(socket)

    def recv_file(self, name: str, dirpath: str) -> None:
        pass

    def send_file(self, name: str, filepath: str) -> None:
        try:
            with open(filepath, "rb") as file:
                while True:

                    block = file.read(BLOCK_SIZE)
                    if not block:
                        break

                    packet = Packet.for_file(block)
                    self.socket.send_all(packet.to_bytes())

                    # TODO: ACK

        except FileNotFoundError:
            raise FileNotFoundError(f"El archivo '{filepath}' no existe.")
        except Exception as e:
            raise RuntimeError(f"Error inesperado: {e}")
