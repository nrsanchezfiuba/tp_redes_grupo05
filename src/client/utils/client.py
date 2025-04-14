class Client:
    def __init__(self, args):
        self.args = args
        self.host = args.host
        self.port = args.port
        self.dst = args.dst
        self.name = args.name
        self.protocol = args.protocol
        self.verbose = args.verbose
        self.quiet = args.quiet

    def run(self):
        self.handle_download()

    def handle_download(self):
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
