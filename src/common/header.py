import struct
from enum import Enum
from typing import NamedTuple, Tuple


class HeaderMasks(Enum):
    PROTOCOLTYPE = 0xC000
    MODE = 0x2000
    SYN = 0x1000
    FIN = 0x800
    ACK = 0x400
    LEN = 0x3FF


class HeaderData(NamedTuple):
    protocol_type: int
    mode: bool
    syn: bool
    fin: bool
    ack: bool
    length: int
    seq_number: int
    ACK_number: int


class Packet:
    def __init__(self, protocol_type: int = 0b00) -> None:
        self.protocol_type: int = protocol_type

    def pack(
        self,
        data: bytes,
        header_data: HeaderData,
    ) -> bytes:
        """
        Packs the data with a custom header.

        Args:
            data (bytes): The data to send.
            syn (bool): Value of the SYN flag.
            fin (bool): Value of the FIN flag.
            ack (bool): Value of the ACK flag.
            mode (bool): Value of the MODE flag.
            options (int, optional): Field for options (if needed). Defaults to None.

        Returns:
            bytes: The complete packet with the header and data.
        """
        header: int = 0

        # Insert Protocol Type
        header |= (self.protocol_type << 14) & HeaderMasks.PROTOCOLTYPE.value

        # Insert Mode
        if header_data.mode:
            header |= HeaderMasks.MODE.value

        # Insert SYN flag
        if header_data.syn:
            header |= HeaderMasks.SYN.value

        # Insert FIN flag
        if header_data.fin:
            header |= HeaderMasks.FIN.value

        # Insert ACK flag
        if header_data.ack:
            header |= HeaderMasks.ACK.value

        # Insert Length of the data
        data_len: int = len(data)
        if (
            data_len > 0x3FF
        ):  # Ensure the length does not exceed the LEN field size (10 bits)
            raise ValueError(
                "Data length exceeds the maximum size of the LEN field (10 bits)."
            )
        header |= data_len & HeaderMasks.LEN.value

        # Pack the header (2 bytes)
        packed_header: bytes = struct.pack(
            ">H", header, header_data.seq_number, header_data.ACK_number
        )

        # Return the header followed by the data
        return packed_header + data

    @staticmethod
    def unpack(packet: bytes) -> Tuple[HeaderData, bytes]:
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

        packed_header: bytes = packet[:2]
        seq_number: bytes = packet[2:4]
        ACK_number: bytes = packet[4:6]
        data: bytes = packet[6:]

        header_int: int = struct.unpack(">H", packed_header)[0]

        protocol_type: int = (header_int & HeaderMasks.PROTOCOLTYPE.value) >> 14
        mode: bool = bool(header_int & HeaderMasks.MODE.value)
        syn: bool = bool(header_int & HeaderMasks.SYN.value)
        fin: bool = bool(header_int & HeaderMasks.FIN.value)
        ack: bool = bool(header_int & HeaderMasks.ACK.value)
        length: int = header_int & HeaderMasks.LEN.value

        header_data = HeaderData(
            protocol_type=protocol_type,
            mode=mode,
            syn=syn,
            fin=fin,
            ack=ack,
            length=length,
            seq_number=int(seq_number),
            ACK_number=int(ACK_number),
        )

        return header_data, data
