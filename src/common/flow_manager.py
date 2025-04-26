import asyncio
from typing import Dict, Tuple

from common.socket.packet import Packet


class FlowManager:
    def __init__(self) -> None:
        """
        FlowManager is responsible for managing the flow of packets in a network application.
        It pushes packets to their respective queue.
        """
        self.flow_table: Dict[Tuple[str, int], asyncio.Queue[Packet]] = dict()

    def add_flow(self, flow: Tuple[str, int]) -> asyncio.Queue[Packet]:
        """
        Adds a new flow to the flow table and returns the associated queue.
        """
        flow_queue: asyncio.Queue[Packet] = asyncio.Queue()
        self.flow_table[flow] = flow_queue
        return flow_queue

    def remove_flow(self, flow: Tuple[str, int]) -> None:
        """
        Removes a flow from the flow table.
        """
        if flow in self.flow_table:
            del self.flow_table[flow]

    def does_flow_exist(self, flow: Tuple[str, int]) -> bool:
        """
        Checks if a flow exists in the flow table.
        """
        return flow in self.flow_table

    async def demultiplex_packet(self, flow: Tuple[str, int], pkt: Packet) -> None:
        """
        Demultiplexes a packet to the appropriate flow queue.
        """
        if flow not in self.flow_table:
            raise ValueError(f"Flow {flow} not found in flow table")
        flow_queue = self.flow_table[flow]
        await flow_queue.put(pkt)
