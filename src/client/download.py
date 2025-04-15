import argparse

from utils.client import Client


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Client to download files from a server.",
        usage="download [-h] [-v | -q] [-H ADDR] [-p PORT] [-d FILEPATH] [-n FILENAME] [-r protocol]",
    )
    parser.add_argument(
        "-v ", "--verbose", action="store_true", help="increase output verbosity"
    )
    parser.add_argument(
        "-q ", "--quiet", action="store_true", help="decrease output verbosity"
    )
    parser.add_argument(
        "-H", "--host", type=str, required=True, metavar="", help="server IP address"
    )
    parser.add_argument(
        "-p", "--port", type=int, required=True, metavar="", help="server port"
    )
    parser.add_argument(
        "-d", "--dst", type=str, required=True, metavar="", help="destination file path"
    )
    parser.add_argument(
        "-n", "--name", type=str, required=True, metavar="", help="file name"
    )
    parser.add_argument(
        "-r",
        "--protocol",
        type=str,
        default="GBN",
        metavar="",
        help="error recovery protocol",
    )

    args = parser.parse_args()

    client = Client(args)
    client.handle_download()


if __name__ == "__main__":
    main()
