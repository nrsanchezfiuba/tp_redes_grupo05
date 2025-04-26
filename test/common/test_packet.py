import unittest

from common.packet import HeaderFlags, HeaderMasks, Packet


class TestPacket(unittest.TestCase):
    def test_syn(self) -> None:
        flags = HeaderFlags.SYN.value
        pckt: Packet = Packet(0, 0, b"", flags=flags)

        # Check raw
        packet_bytes: bytes = pckt.to_bytes()
        self.assertEqual(len(packet_bytes), 6)
        self.assertTrue(int.from_bytes(packet_bytes[:2]) & HeaderMasks.SYN.value)

        # Check rebuilt
        new_pckt = Packet.from_bytes(packet_bytes)
        self.assertTrue(new_pckt.header_data.flags & HeaderMasks.SYN.value)
        self.assertTrue(new_pckt.is_syn())

    def test_ack(self) -> None:
        flags = HeaderFlags.ACK.value
        pckt: Packet = Packet(0, 0, b"", flags=flags)

        # Check raw
        packet_bytes: bytes = pckt.to_bytes()
        self.assertEqual(len(packet_bytes), 6)
        self.assertTrue(int.from_bytes(packet_bytes[:2]) & HeaderMasks.ACK.value)

        # Check rebuilt
        new_pckt = Packet.from_bytes(packet_bytes)
        self.assertTrue(new_pckt.header_data.flags & HeaderMasks.ACK.value)
        self.assertTrue(new_pckt.is_ack())

    def test_fin(self) -> None:
        flags = HeaderFlags.FIN.value
        pckt: Packet = Packet(0, 0, b"", flags=flags)

        # Check raw
        packet_bytes: bytes = pckt.to_bytes()
        self.assertEqual(len(packet_bytes), 6)
        self.assertTrue(int.from_bytes(packet_bytes[:2]), HeaderMasks.FIN.value)

        # Check rebuilt
        new_pckt = Packet.from_bytes(packet_bytes)
        self.assertTrue(new_pckt.header_data.flags & HeaderMasks.FIN.value)
        self.assertTrue(new_pckt.is_fin())

    def test_complete_gbn_upload(self) -> None:
        flags = (
            HeaderFlags.GBN.value
            | HeaderFlags.SYN.value
            | HeaderFlags.ACK.value
            | HeaderFlags.UPLOAD.value
        )
        pckt: Packet = Packet(0, 0, b"ABC", flags=flags)

        # Check raw
        packet_bytes: bytes = pckt.to_bytes()
        self.assertEqual(len(packet_bytes), 6 + len(b"ABC"))
        self.assertEqual(packet_bytes[6:], b"ABC")
        self.assertTrue(int.from_bytes(packet_bytes[:2]) & HeaderMasks.SYN.value)
        self.assertTrue(int.from_bytes(packet_bytes[:2]) & HeaderMasks.ACK.value)
        self.assertTrue(
            int.from_bytes(packet_bytes[:2]) & HeaderMasks.PROTOCOLTYPE.value
        )
        self.assertTrue(int.from_bytes(packet_bytes[:2]) & HeaderMasks.MODE.value)

        # Check rebuilt
        new_pckt = Packet.from_bytes(packet_bytes)
        self.assertEqual(new_pckt.header_data.length, 3)
        self.assertEqual(new_pckt.header_data.seq_number, 0)
        self.assertEqual(new_pckt.header_data.ack_number, 0)
        self.assertEqual(new_pckt.header_data.flags, flags)

        self.assertTrue(new_pckt.header_data.flags & HeaderMasks.SYN.value)
        self.assertTrue(new_pckt.header_data.flags & HeaderMasks.ACK.value)
        self.assertTrue(new_pckt.header_data.flags & HeaderMasks.PROTOCOLTYPE.value)
        self.assertTrue(new_pckt.header_data.flags & HeaderMasks.MODE.value)

        self.assertTrue(new_pckt.is_syn())
        self.assertTrue(new_pckt.is_ack())
        self.assertEqual(new_pckt.get_protocol_type(), HeaderFlags.GBN)
        self.assertEqual(new_pckt.get_mode(), HeaderFlags.UPLOAD)

    def test_complete_sw_download(self) -> None:
        flags = (
            HeaderFlags.STOP_WAIT.value
            | HeaderFlags.SYN.value
            | HeaderFlags.ACK.value
            | HeaderFlags.DOWNLOAD.value
        )
        pckt: Packet = Packet(0, 0, b"ABC", flags=flags)

        # Check raw
        packet_bytes: bytes = pckt.to_bytes()
        self.assertEqual(len(packet_bytes), 6 + len(b"ABC"))
        self.assertEqual(packet_bytes[6:], b"ABC")
        self.assertTrue(int.from_bytes(packet_bytes[:2]) & HeaderMasks.SYN.value)
        self.assertTrue(int.from_bytes(packet_bytes[:2]) & HeaderMasks.ACK.value)
        # should be false S&W=[0b00]
        self.assertFalse(
            int.from_bytes(packet_bytes[:2]) & HeaderMasks.PROTOCOLTYPE.value
        )
        # should be false DOWNLOAD=[0b0]
        self.assertFalse(int.from_bytes(packet_bytes[:2]) & HeaderMasks.MODE.value)

        # Check rebuilt
        new_pckt = Packet.from_bytes(packet_bytes)
        self.assertEqual(new_pckt.header_data.length, 3)
        self.assertEqual(new_pckt.header_data.seq_number, 0)
        self.assertEqual(new_pckt.header_data.ack_number, 0)
        self.assertEqual(new_pckt.header_data.flags, flags)

        self.assertTrue(new_pckt.header_data.flags & HeaderMasks.SYN.value)
        self.assertTrue(new_pckt.header_data.flags & HeaderMasks.ACK.value)
        self.assertFalse(new_pckt.header_data.flags & HeaderMasks.PROTOCOLTYPE.value)
        self.assertFalse(new_pckt.header_data.flags & HeaderMasks.MODE.value)

        self.assertTrue(new_pckt.is_syn())
        self.assertTrue(new_pckt.is_ack())
        self.assertEqual(new_pckt.get_protocol_type(), HeaderFlags.STOP_WAIT)
        self.assertEqual(new_pckt.get_mode(), HeaderFlags.DOWNLOAD)


if __name__ == "__main__":
    unittest.main()
