import asyncio
from typing import Optional, Tuple


class UDPSocket(asyncio.DatagramProtocol):
    def __init__(self) -> None:
        """
        Attributes:
        - transport: The transport object used for sending and receiving data.
        - recv_queue: A queue to store received datagrams along with their sender's address.
        """
        self.transport: Optional[asyncio.transports.DatagramTransport] = None
        self.recv_queue: asyncio.Queue[Tuple[bytes, Tuple[str, int]]] = asyncio.Queue()

    def connection_made(self, transport: asyncio.transports.BaseTransport) -> None:
        """
        Called when a connection is made.

        Args:
        - transport: The transport object for the connection.
        """
        print("[Server] Connection made")
        self.transport = transport  # type: ignore

    def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:
        """
        Called when a datagram is received.

        Args:
        - data (bytes): The received data.
        - addr (Tuple[str, int]): The address of the sender.
        """
        print(f"[*] Data received from {addr}")
        self.recv_queue.put_nowait((data, addr))

    async def bind_connection(self, host: str, port: int) -> None:
        """
        Initializes the UDP connection by binding to the specified host and port.

        Args:
        - host (str): The hostname or IP address to bind to.
        - port (int): The port number to bind to.
        """
        print(f"[Server] Binding to {host}:{port}")
        loop = asyncio.get_running_loop()
        transport, _ = await loop.create_datagram_endpoint(
            lambda: self, local_addr=(host, port)
        )
        self.transport = transport

    async def init_connection(self, host: str, port: int) -> None:
        print(f"[Client] Init connection to {host}:{port}")

        loop = asyncio.get_event_loop()
        transport, _ = await loop.create_datagram_endpoint(
            lambda: self, remote_addr=(host, port)
        )
        self.transport = transport

    async def recv_all(self) -> Tuple[bytes, Tuple[str, int]]:
        """
        Waits until a datagram is received and returns it.

        Returns:
        - Tuple[bytes, Tuple[str, int]]: The received data and the sender's address.
        """
        data, addr = await self.recv_queue.get()
        print(data.decode("utf-8"), addr)
        return data, addr

    def send_all(self, data: bytes, addr: Tuple[str, int]) -> asyncio.Future[None]:
        """
        Sends data to the specified address.

        Args:
        - data (bytes): The data to send.
        - addr (Tuple[str, int]): The address of the recipient (host, port).
        """
        print(f"[*] Sending data to {addr}")
        if self.transport is None:
            raise RuntimeError("Transport is not initialized")
        else:
            self.transport.sendto(data, addr)
        return asyncio.Future()
