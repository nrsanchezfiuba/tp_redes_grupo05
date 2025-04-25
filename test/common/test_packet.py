import unittest

from common.packet import HeaderFlags, Packet


class TestPacket(unittest.TestCase):
    def test_packet(self) -> None:
        flags = HeaderFlags.GBN.value | HeaderFlags.SYN.value | HeaderFlags.ACK.value
        pckt: Packet = Packet(0, 0, b"ABC", flags=flags)
        packet_bytes: bytes = pckt.to_bytes()

        print(f"Packed packet (hex): {packet_bytes.hex()}")
        self.assertEqual(len(packet_bytes), 6 + len(b"ABC"))
        self.assertEqual(packet_bytes[6:], b"ABC")

        # Unpack the packet
        new_pckt = Packet.from_bytes(packet_bytes)

        self.assertEqual(new_pckt.header_data.length, 3)
        self.assertEqual(new_pckt.header_data.seq_number, 0)
        self.assertEqual(new_pckt.header_data.ack_number, 0)
        self.assertEqual(new_pckt.header_data.flags, flags)
        print(f"flags: {hex(new_pckt.header_data.flags)}")
        print(f"mask: {hex(HeaderFlags.SYN.value)}")
        self.assertTrue(new_pckt.header_data.flags & HeaderFlags.SYN.value)
        self.assertTrue(new_pckt.is_ack())
        self.assertTrue(new_pckt.is_syn())
        self.assertTrue(new_pckt.header_data.flags & HeaderFlags.ACK.value)


if __name__ == "__main__":
    unittest.main()
