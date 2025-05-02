from lib.common.args_parser import ArgsParser
from lib.server.server import Server


def main() -> None:
    args_parser = ArgsParser(
        description="Server to receive files from a client.",
        usage="server [-h] [-v | -q] [-H ADDR] [-p PORT] [-s STORAGE] [-r PROTOCOL]",
        include_storage=True,
    )

    server = Server(args_parser.get_arguments())
    server.run()


if __name__ == "__main__":
    main()  # pragma: no cover
