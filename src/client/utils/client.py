from argparse import Namespace


class Client:
    def __init__(self, args: Namespace) -> None:
        self.args: Namespace = args
        self.host: str = args.host
        self.port: int = args.port
        self.dst: str = args.dst
        self.name: str = args.name
        self.protocol: str = args.protocol
        self.verbose: bool = args.verbose
        self.quiet: bool = args.quiet

    def handle_download(self) -> None:
        if self.verbose:
            print("Starting download with the following parameters:")
            print(f"Host: {self.host}")
            print(f"Port: {self.port}")
            print(f"Destination Path: {self.dst}")
            print(f"File Name: {self.name}")
            print(f"Protocol: {self.protocol}")
        elif self.quiet:
            pass  # Suppress output
        else:
            print("Downloading file...")

        # Add your download logic here
        print("Download complete.")

    def handle_upload(self) -> None:
        if self.verbose:
            print("Starting upload with the following parameters:")
            print(f"Host: {self.host}")
            print(f"Port: {self.port}")
            print(f"Source Path: {self.dst}")
            print(f"File Name: {self.name}")
            print(f"Protocol: {self.protocol}")
        elif self.quiet:
            pass
        else:
            print("Uploading file...")
