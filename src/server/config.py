from argparse import Namespace
import os

from common.skt.packet import HeaderFlags
from common.protocol.protocol import protocol_mapping


class ServerConfig:
    def __init__(
        self,
        args: Namespace,
    ):
        self.host: str = args.host
        self.port: int = args.port
        self.dirpath: str = args.storage
        self.protocol_type: HeaderFlags = self._map_protocol(args.protocol)
        self.verbose: bool = args.verbose
        self.quiet: bool = args.quiet

        # Create the directory if it doesn't exist
        os.makedirs(self.dirpath, exist_ok=True)

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
