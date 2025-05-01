import os
from argparse import Namespace

from common.protocol.protocol import protocol_mapping
from common.skt.packet import HeaderFlags


class Config:
    def __init__(
        self,
        args: Namespace,
    ):
        self.host: str = args.host
        self.port: int = args.port
        self.protocol_type: HeaderFlags = self._map_protocol(args.protocol)
        self.verbose: bool = args.verbose
        self.quiet: bool = args.quiet

        storage: str = ""

        # Server only
        if hasattr(args, "storage"):
            self.dirpath: str = args.storage
            storage = self.dirpath

        # Client only
        if hasattr(args, "dst"):
            self.dst: str = args.dst
            self.name: str = args.name
            storage = self.dst

        # Create the directory if it doesn't exist
        if storage:
            os.makedirs(storage, exist_ok=True)

    def __repr__(self):
        return (
            f"ServerConfig(host={self.host}, "
            f"port={self.port}, "
            f"dirpath={self.dirpath}, "
            f"protocol_type={self.protocol_type}, "
            f"verbose={self.verbose}, "
            f"quiet={self.quiet})"
        )

    def _map_protocol(self, protocol: str) -> HeaderFlags:
        if protocol not in protocol_mapping:
            raise ValueError(f"Invalid protocol: {protocol}")
        return protocol_mapping[protocol]
