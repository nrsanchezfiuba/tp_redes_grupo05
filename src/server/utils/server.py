from argparse import Namespace


class Server:
    def __init__(self, args: Namespace) -> None:
        self.args: Namespace = args
        self.host: str = args.host
        self.port: int = args.port
        self.storage: str = args.storage
        self.name: str = args.name
        self.protocol: str = args.protocol
        self.verbose: bool = args.verbose
        self.quiet: bool = args.quiet

    def run(self) -> None:
        if self.verbose:
            print("Starting server with the following parameters:")
            print(f"Host: {self.host}")
            print(f"Port: {self.port}")
            print(f"storage folder dir path: {self.storage}")
            print(f"File Name: {self.name}")
            print(f"Protocol: {self.protocol}")
        elif self.quiet:
            pass  # Suppress output
        else:
            print("Start Server...")
