import asyncio
from typing import Tuple

from common.flow_manager import FlowManager
from common.skt.connection_socket import ConnectionSocket
from common.skt.packet import HeaderFlags, Packet
from common.skt.udp_socket import UDPSocket


class AcceptorSocket:
    def __init__(self, proto_type: HeaderFlags, flow_manager: FlowManager):
        """
        AcceptorSocket is responsible for accepting incoming connections
        and demultiplexing packets to the appropriate flow queue.
        """
        if proto_type not in (HeaderFlags.GBN, HeaderFlags.SW):
            raise ValueError("Invalid protocol type")
        self.proto_type = proto_type
        self.udp_skt = UDPSocket()
        self.flow_manager = flow_manager

    def bind(self, host: str, port: int) -> None:
        """
        Binds the socket to the specified host and port.
        """
        self.udp_skt.bind(host, port)

    async def accept(self) -> ConnectionSocket:
        """
        Accepts incomming connections,
        validates the incomming connection by:
            - checking SYN flag
            - checking for compatible protocol_type
        Demultiplexes incomming messages from conneted processes
        """
        while True:
            data, sender = await self.udp_skt.recv_all()
            pkt = Packet.from_bytes(data)
            print(f"[AcceptorSocket] Received packet: {pkt}")

            if self._is_protocol_invalid(pkt):
                await self._send_fin(sender)
            elif pkt.is_syn():
                print(f"[AcceptorSocket] SYN packet received from {sender}")
                # Hanshake the new connection
                q: asyncio.Queue[Packet] = self.flow_manager.add_flow(sender)
                await self._send_syn_ack(sender)
                return await ConnectionSocket.for_server(sender, q, self.proto_type)
            elif pkt.is_fin():
                await self.flow_manager.demultiplex_packet(sender, pkt)
                self.flow_manager.remove_flow(sender)
            else:
                await self.flow_manager.demultiplex_packet(sender, pkt)

    def _is_protocol_invalid(self, pkt: Packet) -> bool:
        return pkt.get_protocol_type() != self.proto_type

    async def _send_syn_ack(self, sender: Tuple[str, int]) -> None:
        syn_ack_pkt = Packet(
            flags=HeaderFlags.SYN.value | HeaderFlags.ACK.value | self.proto_type.value,
        )
        await self.udp_skt.send_all(syn_ack_pkt.to_bytes(), sender)

    async def _send_fin(self, sender: Tuple[str, int]) -> None:
        fin_pkt = Packet(
            flags=HeaderFlags.FIN.value | self.proto_type.value,
        )
        await self.udp_skt.send_all(fin_pkt.to_bytes(), sender)
