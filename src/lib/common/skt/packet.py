import struct
from enum import Enum
from typing import NamedTuple

HEADER_PACK_FORMAT: str = "!HHH"  # Big-endian unsigned short (2 bytes)

MAX_SEQ_NUM: int = 65536


class HeaderMasks(Enum):
    PROTOCOLTYPE = 0xC000  # 1100_0000_0000_0000
    MODE = 0x2000  # 0010_0000_0000_0000
    SYN = 0x1000  # 0001_0000_0000_0000
    FIN = 0x0800  # 0000_1000_0000_0000
    ACK = 0x0400  # 0000_0100_0000_0000
    LEN = 0x03FF  # 0000_0011_1111_1111


class HeaderFlags(Enum):
    SW = 0x0000
    GBN = 0x4000
    UPLOAD = 0x2000
    DOWNLOAD = 0x0000
    SYN = 0x1000
    FIN = 0x0800
    ACK = 0x0400
    NONE = 0xFFFF


class HeaderData(NamedTuple):
    """
    Represents a header of 6 bytes that includes:
    - flags: 6 bits
    - length: 10 bits
    - seq_number: 16 bits
    - ACK_number: 16 bits
    """

    flags: int
    length: int
    seq_num: int
    ack_num: int


class Packet:
    @classmethod
    def for_ack(cls, seq_num: int, ack_num: int, protocol: HeaderFlags) -> "Packet":
        return cls(seq_num, ack_num, b"", HeaderFlags.ACK.value | protocol.value)

    @classmethod
    def from_bytes(cls, packet: bytes) -> "Packet":
        """
        Creates a Packet instance from a byte array (from network).
        """
        if len(packet) < 6:
            raise ValueError("Packet too short to contain a header.")

        data: bytes = packet[6:]

        flags_and_length, seq_num, ack_num = struct.unpack(
            HEADER_PACK_FORMAT, packet[:6]
        )

        flags = flags_and_length & (~HeaderMasks.LEN.value)
        length = flags_and_length & HeaderMasks.LEN.value

        return cls(seq_num, ack_num, data, flags=flags, length=length)

    def to_bytes(self) -> bytes:
        """
        Coverts Self to bytes (ready to send over network).
        """

        data_len: int = len(self.data)
        if data_len > HeaderMasks.LEN.value:
            raise ValueError("Data exceeds the maximum size [2^10B].")

        flags_and_length = self.header_data.flags | data_len

        # Pack the header in 6 bytes
        packed_header: bytes = struct.pack(
            HEADER_PACK_FORMAT,
            flags_and_length,
            self.header_data.seq_num,
            self.header_data.ack_num,
        )

        # Return the header followed by the data
        return packed_header + self.data

    def __init__(
        self,
        seq_num: int = 0,
        ack_num: int = 0,
        data: bytes = b"",
        flags: int = 0,
        length: int = 0,
    ) -> None:
        self.header_data = HeaderData(
            flags=flags,
            length=length if length else len(data),
            seq_num=seq_num,
            ack_num=ack_num,
        )
        self.data = data

    def __repr__(self) -> str:
        return (
            f"Packet(flags={hex(self.header_data.flags)}, "
            f"length={self.header_data.length}, "
            f"seq_num={self.header_data.seq_num}, "
            f"ack_num={self.header_data.ack_num}, "
            f"data={self.data[:8]!r})"
        )

    def is_syn(self) -> bool:
        return bool(self.header_data.flags & HeaderMasks.SYN.value)

    def is_fin(self) -> bool:
        return bool(self.header_data.flags & HeaderMasks.FIN.value)

    def is_ack(self) -> bool:
        return bool(self.header_data.flags & HeaderMasks.ACK.value)

    def get_mode(self) -> HeaderFlags:
        return HeaderFlags(self.header_data.flags & HeaderMasks.MODE.value)

    def get_protocol_type(self) -> HeaderFlags:
        return HeaderFlags(self.header_data.flags & HeaderMasks.PROTOCOLTYPE.value)

    def get_ack_num(self) -> int:
        return self.header_data.ack_num

    def get_seq_num(self) -> int:
        return self.header_data.seq_num

    def get_data(self) -> bytes:
        return self.data
