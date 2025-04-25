import unittest
from ctypes import c_uint16

from common.packet import HeaderData, HeaderFlags, Packet


class TestPacket(unittest.TestCase):
    def test_packet(self) -> None:
        header_data: HeaderData = HeaderData(
            flags=c_uint16(
                HeaderFlags.GBN.value | HeaderFlags.SYN.value | HeaderFlags.ACK.value
            ),
            length=c_uint16(0),
            seq_number=c_uint16(0),
            ACK_number=c_uint16(0),
        )
        pckt: Packet = Packet(header_data, b"ABC")
        packet_bytes: bytes = pckt.to_bytes()

        print(f"Packed packet (hex): {packet_bytes.hex()}")
        self.assertEqual(len(packet_bytes), 6 + len(b"ABC"))
        self.assertEqual(packet_bytes[6:], b"ABC")

        # Unpack the packet
        new_pckt = Packet.from_bytes(packet_bytes)

        self.assertEqual(int.from_bytes(new_pckt.header_data.length), 3)
        self.assertEqual(
            int.from_bytes(new_pckt.header_data.seq_number),
            int.from_bytes(header_data.seq_number),
        )
        self.assertEqual(
            int.from_bytes(new_pckt.header_data.ACK_number),
            int.from_bytes(header_data.ACK_number),
        )
        self.assertEqual(
            int.from_bytes(new_pckt.header_data.flags),
            int.from_bytes(header_data.flags),
        )
        print(f"flags: {hex(new_pckt.header_data.flags.value)}")
        print(f"mask: {hex(HeaderFlags.SYN.value)}")
        self.assertTrue(new_pckt.header_data.flags.value & HeaderFlags.SYN.value)
        self.assertTrue(new_pckt.is_ack())
        self.assertTrue(new_pckt.header_data.flags.value & HeaderFlags.ACK.value)


if __name__ == "__main__":
    unittest.main()
