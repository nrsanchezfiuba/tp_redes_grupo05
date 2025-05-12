from lib.client.client import Client
from lib.common.args_parser import ArgsParser
from lib.common.timer import timer


@timer
def upload() -> None:
    args_parser = ArgsParser(
        description="Client to upload files from a server.",
        usage="upload [-h] [-v | -q] [-H ADDR] [-p PORT] [-d FILEPATH] [-n FILENAME] [-r protocol]",
        include_destination=True,
        include_filename=True,
    )
    client = Client(args_parser.get_arguments(), "upload")
    client.run()
    print(f"[UPLOAD] successfully uploaded {args_parser.get_arguments().name}.")


if __name__ == "__main__":
    upload()  # pragma: no cover
