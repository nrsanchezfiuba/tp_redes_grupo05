from abc import ABC, abstractmethod

BLOCK_SIZE = 1000


class Protocol(ABC):
    def __init__(self, socket):  # type: ignore
        self.socket = socket

    @abstractmethod
    def recv_file(self, name: str, dirpath: str) -> None:
        pass

    @abstractmethod
    def send_file(self, name: str, filepath: str) -> None:
        pass
