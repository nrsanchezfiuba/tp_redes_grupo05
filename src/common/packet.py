import struct
from ctypes import c_uint16
from enum import Enum
from typing import NamedTuple

HEADER_PACK_FORMAT: str = "!HHH"  # Big-endian unsigned short (2 bytes)


class HeaderMasks(Enum):
    PROTOCOLTYPE = 0xC000  # 1100_0000_0000_0000
    MODE = 0x2000
    SYN = 0x1000  # 0001_0000_0000_0000
    FIN = 0x0800
    ACK = 0x0400  # 0000_0100_0000_0000
    LEN = 0x03FF  # 0011_1111_1111


class HeaderFlags(Enum):
    STOP_WAIT = 0x0000
    GBN = 0x4000
    MODE = 0x2000
    SYN = 0x1000
    FIN = 0x0800
    ACK = 0x0400


# TODO: Change types to int
class HeaderData(NamedTuple):
    flags: c_uint16  # 6 bits
    length: c_uint16  # 10 bits
    seq_number: c_uint16  # 16 bits
    ACK_number: c_uint16  # 16 bits


# TODO: Update the methods documentation
class Packet:
    @classmethod
    def from_bytes(cls, packet: bytes) -> "Packet":
        """
        Unpacks a received packet to separate the header fields and the data.

        Args:
            packet (bytes): The received packet.

        Returns:
            Tuple[HeaderData, bytes]: A tuple containing a HeaderData namedtuple
                                    with the header fields and the data as bytes.
        """
        if len(packet) < 6:
            raise ValueError("Packet too short to contain a header.")

        data: bytes = packet[6:]

        flags_and_length, seq_num, ack_num = struct.unpack(
            HEADER_PACK_FORMAT, packet[:6]
        )

        flags = c_uint16(flags_and_length & (~HeaderMasks.LEN.value))
        length = c_uint16(flags_and_length & HeaderMasks.LEN.value)

        header_data = HeaderData(
            flags=flags,
            length=length,
            seq_number=c_uint16(seq_num),
            ACK_number=c_uint16(ack_num),
        )

        return cls(header_data, data)

    def __init__(self, header_data: HeaderData, data: bytes) -> None:
        self.header_data = header_data
        self.data = data

    def to_bytes(self) -> bytes:
        """
        Packs the data with a custom header.

        Args:
            flags (int): The flags to set in the header.
            seq_number (int): The sequence number.
            ack_number (int): The acknowledgment number.
            data (bytes): The data to send.

        Returns:
            bytes: The complete packet with the header and data.
        """

        # Insert Length of the data
        data_len: int = len(self.data)
        if (
            data_len > HeaderMasks.LEN.value
        ):  # Ensure the length does not exceed the LEN field size (10 bits)
            raise ValueError(
                "Data length exceeds the maximum size of the LEN field (10 bits)."
            )

        flags_and_length: c_uint16 = c_uint16(
            (int.from_bytes(self.header_data.flags) | data_len)
        )

        # Pack the header (by 2 bytes per field)
        packed_header: bytes = struct.pack(
            HEADER_PACK_FORMAT,
            int.from_bytes(flags_and_length),
            int.from_bytes(self.header_data.seq_number),
            int.from_bytes(self.header_data.ACK_number),
        )

        # Return the header followed by the data
        return packed_header + self.data

    def is_ack(self) -> bool:
        return bool(self.header_data.flags.value & HeaderMasks.ACK.value)
