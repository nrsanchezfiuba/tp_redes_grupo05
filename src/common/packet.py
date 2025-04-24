import struct
from typing import Type


class Packet:
    @classmethod
    def for_file(cls: Type["Packet"], file_content: bytes) -> "Packet":
        return cls(0, 0, 0, 0, 0, 0, 0, 0, b"")

    @classmethod
    def from_bytes(cls: Type["Packet"], raw_bytes: bytes) -> "Packet":
        header, seq_number, ack_number = struct.unpack("!HHH", raw_bytes[:6])

        protocol_type: int = (header >> 15) & 0b1
        mode: int = (header >> 14) & 0b1
        syn: int = (header >> 13) & 0b1
        fin: int = (header >> 12) & 0b1
        ack: int = (header >> 11) & 0b1
        length: int = header & 0x7FF

        data: bytes = raw_bytes[6:]

        return cls(
            protocol_type, mode, syn, fin, ack, length, seq_number, ack_number, data
        )

    def __init__(
        self,
        protocol_type: int,
        mode: int,
        syn: int,
        fin: int,
        ack: int,
        length: int,
        seq_number: int,
        ack_number: int,
        data: bytes,
    ) -> None:
        self.protocol_type: int = protocol_type  # 1 bit
        self.mode: int = mode  # 1 bit
        self.syn: int = syn  # 1 bit
        self.fin: int = fin  # 1 bit
        self.ack: int = ack  # 1 bit
        self.length: int = length  # 11 bits
        self.seq_number: int = seq_number  # 16 bits
        self.ack_number: int = ack_number  # 16 bits
        self.data: bytes = data  # n bytes

    def to_bytes(self) -> bytes:
        # First pack the first 16 bits (header) manually
        header: int = (
            (self.protocol_type & 0b1) << 15
            | (self.mode & 0b1) << 14
            | (self.syn & 0b1) << 13
            | (self.fin & 0b1) << 12
            | (self.ack & 0b1) << 11
            | (self.length & 0x7FF)  # 11 bits for length
        )
        # Pack header (16 bits), seq_number (16 bits), ack_number (16 bits)
        packed: bytes = struct.pack("!HHH", header, self.seq_number, self.ack_number)
        return packed + self.data
