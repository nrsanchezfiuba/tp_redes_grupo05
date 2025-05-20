import argparse
import os
import time
from typing import Any

from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.topo import Topo

SERVER_PORT = 7532


class ClientServerTopo(Topo):  # type: ignore
    def __init__(self, num_clients: int = 1, **opts: Any) -> None:
        self.num_clients = num_clients
        super().__init__(**opts)

    def build(self, **_opts: Any) -> None:
        server_ip = "10.0.0.1"
        server = self.addHost("h1", ip=server_ip)
        s1 = self.addSwitch("s1")

        self.addLink(server, s1, cls=TCLink, loss=5)

        for i in range(2, self.num_clients + 2):
            client_name = f"h{i}"
            client_host = self.addHost(client_name, ip=f"10.0.0.{i}")
            self.addLink(client_host, s1, cls=TCLink, loss=5)


def create_file(file_path: str, size_kb: int = 10) -> None:
    chunk = os.urandom(1024)
    with open(file_path, "wb") as f:
        for _ in range(size_kb):
            f.write(chunk)
    print(f"Created file {file_path} ({size_kb}KB)")


def create_dirs_and_files(dirpath: str, filename: str, file_size_kb: int = 10) -> None:
    os.makedirs(dirpath, exist_ok=True)
    print(f"Created client directory: {dirpath}")

    file_path = os.path.join(dirpath, filename)
    create_file(file_path, file_size_kb)


def run(num_clients: int, recovery_protocol: str) -> None:
    server_path = "./server_files"
    os.makedirs(server_path, exist_ok=True)

    for i in range(2, num_clients + 2):
        client_path = f"./client_{i}_files"
        filename = f"client_file_{i}"
        create_dirs_and_files(client_path, filename, file_size_kb=5120)

    topo = ClientServerTopo(num_clients=num_clients)
    net = Mininet(topo=topo)
    net.start()

    server = net.get("h1")
    server_command = (
        f'xterm -hold -e "PYTHONPATH=src python3 ./src/start_server.py '
        f"-v -H 10.0.0.1 -p {SERVER_PORT} -s {server_path} "
        f'-r {recovery_protocol}" &'
    )
    server.cmd(server_command)
    time.sleep(0.5)

    CLI(net)
    net.stop()


if __name__ == "__main__":
    setLogLevel("info")

    parser = argparse.ArgumentParser(
        description="Mininet topology with configurable clients and 5% packet loss"
    )
    parser.add_argument(
        "--clients", type=int, default=3, help="Number of clients (default: 3)"
    )
    parser.add_argument(
        "--r",
        type=str,
        choices=["GBN", "SW"],
        default="SW",
        help="Recovery protocol: GBN (Go-Back-N) or SW (Stop-and-Wait) (default: SW)",
    )
    args = parser.parse_args()

    run(args.clients, args.r)
