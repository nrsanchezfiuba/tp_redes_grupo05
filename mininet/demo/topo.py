import json
import os
import sys
import time
from typing import Any, Dict

from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.topo import Topo

SERVER_PORT = 7532


class ClientServerTopo(Topo):  # type: ignore
    def __init__(self, config: Dict[str, Any], **opts: Any) -> None:
        self.loss = config.get("loss_percentage")
        self.clients = config.get("clients")
        self.protocol = config.get("recovery_protocol")
        self.server_storage_path = config.get("server_path")

        self.actions: Dict[str, str] = dict()
        super().__init__(**opts)

    def build(self, **_opts: Any) -> None:
        # Calculate loss percentage divided by the number of clients
        if self.loss is None or not self.clients:
            raise ValueError(
                "Loss percentage and clients must be properly defined in the configuration."
            )
        loss = self.loss / 2

        # Create server (h1) and switch (s1)
        server_ip = "10.0.0.1"
        server = self.addHost("h1", ip=server_ip)
        s1 = self.addSwitch("s1")
        self.addLink(server, s1, cls=TCLink, loss=loss)

        for i, _ in enumerate(self.clients, start=2):
            client_name = f"h{i}"
            client_host = self.addHost(client_name)
            self.addLink(client_host, s1)


def create_file(file_path: str, size_kb: int = 10) -> None:
    chunk = os.urandom(1024)

    with open(file_path, "ab") as f:
        for _ in range(size_kb):
            f.write(chunk)

    print(f"Created file {file_path} ({size_kb}KB)")


def create_dirs_and_files(dirpath: str, filename: str, file_size_kb: int = 10) -> None:
    os.makedirs(dirpath, exist_ok=True)
    print(f"Created client directory: {dirpath}")

    file_path = os.path.join(dirpath, filename)
    create_file(file_path, file_size_kb)


def compare_outputs(config: Dict[str, Any]) -> None:
    server_path = config.get("server_path")
    clients = config.get("clients")
    if not clients:
        raise ValueError("Clients must be properly defined in the configuration.")
    for client in clients:
        client_path = client.get("path")
        compare_file = client.get("file")
        compare_command = f"./check_hash.sh ./{server_path}/{compare_file} ./{client_path}/{compare_file}"
        result = os.popen(compare_command).read()
        print(f"File: {compare_file}: {result.strip()}")


def run(config_file: str) -> None:
    with open(config_file) as f:
        config = json.load(f)
        verify_config(config)

    topo = ClientServerTopo(config)
    net = Mininet(topo=topo)
    net.start()
    handle_actions(net, config)

    CLI(net)

    net.stop()


def handle_actions(net: Mininet, config) -> None:  # type: ignore
    server = net.get("h1")
    server_command = f'xterm -hold -e "PYTHONPATH=src python3 ./src/start_server.py -v -H 10.0.0.1 -p {SERVER_PORT} -s {config["server_path"]} -r {config["recovery_protocol"]}" &'
    server.cmd(server_command)

    time.sleep(0.5)

    for i, client in enumerate(config["clients"], start=2):
        client_command = f'xterm -hold -e "PYTHONPATH=src python3 ./src/{client["action"]}.py -v -H 10.0.0.1 -p {SERVER_PORT} -n {client["file"]} -d {client["path"]} -r {config["recovery_protocol"]}" &'
        client_host = net.get(f"h{i}")
        client_host.cmd(client_command)


def verify_config(config: Dict[str, Any]) -> None:
    for client in config["clients"]:
        if not os.path.exists(client["path"]):
            if client["action"] == "upload":
                create_dirs_and_files(client["path"], client["file"], file_size_kb=10)
            elif client["action"] == "download":
                create_dirs_and_files(
                    config["server_path"], client["file"], file_size_kb=10
                )


if __name__ == "__main__":
    setLogLevel("info")

    if len(sys.argv) < 2:
        print("Usage: python topology.py <config_file.json>")
        sys.exit(1)

    config_file = sys.argv[1]
    run(config_file)
