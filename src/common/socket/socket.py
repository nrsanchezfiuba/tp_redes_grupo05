from common.socket.packet import HeaderFlags, Packet
from common.socket.udp_socket import UDPSocket


class Socket:
    def __init__(self, proto_type: HeaderFlags):  # take in FlowManager
        if proto_type not in (HeaderFlags.GBN, HeaderFlags.STOP_WAIT):
            raise ValueError("Invalid protocol type")
        self.proto_type = proto_type
        self.udp_skt = UDPSocket()

    async def bind(self, host: str, port: int) -> None:
        await self.udp_skt.init_connection(host, port)

    async def accept(self) -> None:
        data, sender = await self.udp_skt.recv_all()  # SYN
        pkt = Packet.from_bytes(data)
        if not pkt.is_syn():
            raise ValueError("Invalid packet type, expected SYN")
        elif pkt.get_protocol_type() != self.proto_type:
            # Send fin if incompatible protocol
            fin_pkt = Packet(flags=HeaderFlags.FIN.value)
            self.udp_skt.send_all(fin_pkt.to_bytes(), sender)
        else:
            # TODO demultiplex flow
            pass

        syn_ack_pkt = Packet(
            flags=HeaderFlags.SYN.value | HeaderFlags.ACK.value,
        )
        self.udp_skt.send_all(syn_ack_pkt.to_bytes(), sender)

        # Create a new connection socket
        # increment seq num
        # set ack number
        # send SYN, ACK

    async def connect(
        self, host: str, port: int, file_name: str, mode: HeaderFlags
    ) -> None:
        if mode not in (HeaderFlags.UPLOAD, HeaderFlags.DOWNLOAD):
            raise ValueError("Invalid mode, expected UPLOAD or DOWNLOAD")

        # Send SYN
        syn_pkt = Packet(
            flags=HeaderFlags.SYN.value,
        )
        await self.udp_skt.send_all(syn_pkt.to_bytes(), (host, port))

        # await for SYN ACK
        _, _ = await self.udp_skt.recv_all()

    def send(self, data: bytes) -> None:
        # TODO handle packet logic
        # Increment seq num, ack num
        pass

    def recv(self, bufsize: int) -> bytes:
        # TODO handle packet logic
        # Increment seq num, ack num
        return b""
