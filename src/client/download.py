from client.utils.client import Client
from common.args_parser import ArgsParser


def main() -> None:
    args_parser = ArgsParser(
        description="Client to download files from a server.",
        usage="download [-h] [-v | -q] [-H ADDR] [-p PORT] [-d FILEPATH] [-n FILENAME] [-r protocol]",
        include_destination=True,
        include_filename=True,
    )
    client = Client(args_parser.get_arguments())
    client.run()


if __name__ == "__main__":
    main()  # pragma: no cover
