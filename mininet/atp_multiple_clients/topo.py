import json
import os
import random
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
        loss = self.loss / len(self.clients)

        # Create server (h1) and switch (s1)
        server_ip = "10.0.0.1"
        server = self.addHost("h1", ip=server_ip)
        s1 = self.addSwitch("s1")
        self.addLink(server, s1, cls=TCLink, loss=loss)
        server_command = f"PYTHONPATH=src python3 ./src/start_server.py -v -H {server_ip} -p {SERVER_PORT} -s {self.server_storage_path} -r {self.protocol} --log-file mn_server.log"
        self.actions[server] = server_command

        # Create clients based on config
        if not isinstance(self.clients, list):
            raise ValueError("Clients must be a list.")

        for i, client_config in enumerate(self.clients, start=2):
            client_name = f"h{i}"
            client_host = self.addHost(client_name)
            self.addLink(client_host, s1, cls=TCLink, loss=loss)

            client_command = f"PYTHONPATH=src python3 ./src/{client_config['action']}.py -v -H {server_ip} -p {SERVER_PORT} -n {client_config['file']} -d {client_config['path']} -r {self.protocol} --log-file mn_client{i-1}.log && echo client {i-1} done"
            self.actions[client_host] = client_command


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
    # Load configuration from JSON file
    with open(config_file) as f:
        config = json.load(f)
        verify_config(config)

    # Create topology
    topo = ClientServerTopo(config)
    topo_actions = topo.actions
    net = Mininet(topo=topo)
    net.start()
    handle_actions(net, topo_actions)

    compare_outputs(config)

    net.stop()


def handle_actions(net: Mininet, actions=Dict) -> None:  # type: ignore
    venv_command = "source .venv/bin/activate && "

    # Start server
    server = net.get("h1")
    server_command = actions[server.name]
    full_server_command = f'bash -c "{venv_command}{server_command}"'
    print(f"Starting server [{server}] with command: [{full_server_command}]")
    server_process = server.popen(
        full_server_command, stdout=sys.stdout, stderr=sys.stderr, shell=True
    )

    # Start clients
    client_processes = []
    for client in net.hosts[1:]:
        time.sleep(random.uniform(0, 2))
        client_command = actions[client.name]
        full_client_command = f'bash -c "{venv_command}{client_command}"'
        print(f"Starting client [{client}] with command: [{full_client_command}]")
        client_process = client.popen(
            full_client_command, stdout=sys.stdout, stderr=sys.stderr, shell=True
        )
        client_processes.append(client_process)

    # Start CLI
    CLI(net)

    # Terminate all processes after CLI exits
    server_process.terminate()
    for client_process in client_processes:
        client_process.terminate()


def verify_config(config: Dict[str, Any]) -> None:
    required_fields = ["clients", "loss_percentage", "recovery_protocol", "server_path"]
    required_client_fields = ["action", "file", "path"]
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required field: {field}")

    if not isinstance(config.get("clients"), list):
        raise ValueError("Clients should be a list")

        # Ensure all clients have required fields
    for client in config["clients"]:
        if not isinstance(client, dict):
            raise ValueError("Each client should be a dictionary")
        if not all(key in client for key in required_client_fields):
            raise ValueError(
                "Each client must have 'action', 'file', and 'path' fields"
            )
        if not os.path.exists(client["path"]):
            raise ValueError(f"Path does not exist for client: {client['path']}")


if __name__ == "__main__":
    setLogLevel("info")

    if len(sys.argv) < 2:
        print("Usage: python topology.py <config_file.json>")
        sys.exit(1)

    config_file = sys.argv[1]
    run(config_file)
