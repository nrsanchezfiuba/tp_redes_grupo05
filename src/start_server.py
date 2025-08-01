from lib.common.args_parser import ArgsParser
from lib.common.timer import timer
from lib.server.server import Server


@timer
def start_server() -> None:
    args_parser = ArgsParser(
        description="Server to receive files from a client.",
        usage="server [-h] [-v | -q] [-H ADDR] [-p PORT] [-s STORAGE] [-r PROTOCOL]",
        include_storage=True,
    )

    server = Server(args_parser.get_arguments())
    server.run()


if __name__ == "__main__":
    start_server()  # pragma: no cover
