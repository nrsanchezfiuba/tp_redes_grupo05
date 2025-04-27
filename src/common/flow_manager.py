import asyncio
from typing import Dict, Tuple

from common.skt.packet import Packet


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
        if flow in self.flow_table:
            raise ValueError(f"Flow {flow} already exists in flow table")
        flow_queue: asyncio.Queue[Packet] = asyncio.Queue()
        self.flow_table[flow] = flow_queue
        return flow_queue

    def remove_flow(self, flow: Tuple[str, int]) -> None:
        """
        Removes a flow from the flow table.
        """
        if flow in self.flow_table:
            del self.flow_table[flow]

    async def demultiplex_packet(self, flow: Tuple[str, int], pkt: Packet) -> None:
        """
        Demultiplexes a packet to the appropriate flow queue.
        """
        print(f"Demultiplex packet {pkt} to flow {flow}")
        if flow not in self.flow_table:
            raise ValueError(f"Flow {flow} not found in flow table")
        flow_queue = self.flow_table[flow]
        await flow_queue.put(pkt)


# TODO check to remove laater
if __name__ == "__main__":
    # Example usage
    flow_manager = FlowManager()
    flow = ("127.0.0.1", 8080)
    flow_queue: asyncio.Queue[Packet] = flow_manager.add_flow(flow)

    async def consumer() -> None:
        while True:
            pkt = await flow_queue.get()
            print(f"Received packet: {pkt}")
            flow_queue.task_done()

    async def producer() -> None:
        num = 0
        while True:
            pkt = Packet(seq_num=num, ack_num=num, data=b"Hello")
            await flow_manager.demultiplex_packet(flow, pkt)
            print(f"Sent packet: {pkt}")
            num += 1
            await asyncio.sleep(1)

    asyncio.run(producer())
    asyncio.run(consumer())
