import argparse

from server.utils.server import Server


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Server initialization",
        usage="start_server [-h] [-v | -q] [-H ADDR] [-p PORT] [-s DIRPATH] [-n FILENAME] [-r protocol]",
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
        "-s", "--storage", type=str, required=True, metavar="", help="storage dir path"
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

    server = Server(args)
    server.run()


if __name__ == "__main__":
    main()  # pragma: no cover
