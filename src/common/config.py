import os
from argparse import Namespace

from common.skt.packet import HeaderFlags

protocol_mapping = {
    "SW": HeaderFlags.STOP_WAIT,
    "GBN": HeaderFlags.GBN,
}

mode_mapping = {
    "upload": HeaderFlags.UPLOAD,
    "download": HeaderFlags.DOWNLOAD,
}


class Config:
    def __init__(
        self,
        args: Namespace,
        client: bool = False,
        server: bool = False,
        client_mode: str = "",
    ):
        self.host: str = args.host
        self.port: int = args.port
        self.protocol_type: HeaderFlags = self._map_protocol(args.protocol)
        self.verbose: bool = args.verbose
        self.quiet: bool = args.quiet

        storage: str = ""

        # Server only
        if server:
            self.server_dirpath: str = args.storage
            storage = self.server_dirpath

        # Client only
        if client:
            self.client_dst: str = args.dst
            self.client_filename: str = args.name
            self.client_mode: HeaderFlags = self._map_mode(client_mode)
            storage = self.client_dst

        # Create the directory if it doesn't exist
        if storage:
            os.makedirs(storage, exist_ok=True)

    def _map_protocol(self, protocol: str) -> HeaderFlags:
        if protocol not in protocol_mapping:
            raise ValueError(f"Invalid protocol: {protocol}")
        return protocol_mapping[protocol]

    def _map_mode(self, mode: str) -> HeaderFlags:
        if mode not in mode_mapping:
            raise ValueError(f"Invalid mode: {mode}")
        return mode_mapping[mode]
