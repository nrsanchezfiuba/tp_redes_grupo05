from lib.client.client import Client
from lib.common.args_parser import ArgsParser
from lib.common.timer import timer


@timer
def download() -> None:
    args_parser = ArgsParser(
        description="Client to download files from a server.",
        usage="download [-h] [-v | -q] [-H ADDR] [-p PORT] [-d FILEPATH] [-n FILENAME] [-r protocol]",
        include_destination=True,
        include_filename=True,
    )
    client = Client(args_parser.get_arguments(), "download")
    client.run()
    print(f"[DOWNLOAD] successfully downloaded {args_parser.get_arguments().name}.")


if __name__ == "__main__":
    download()  # pragma: no cover
