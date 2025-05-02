import argparse
from typing import Any, List, Mapping, Tuple


class ArgsParser:
    def __init__(
        self,
        description: str,
        usage: str,
        include_storage: bool = False,
        include_destination: bool = False,
        include_filename: bool = False,
    ) -> None:
        self.parser = argparse.ArgumentParser(description=description, usage=usage)
        self.include_storage = include_storage
        self.include_destination = include_destination
        self.include_filename = include_filename
        self._add_arguments()

    def _add_arguments(self) -> None:
        common_args: List[Tuple[List[str], Mapping[str, Any]]] = [
            (
                ["-v", "--verbose"],
                {"action": "store_true", "help": "increase output verbosity"},
            ),
            (
                ["-q", "--quiet"],
                {"action": "store_true", "help": "decrease output verbosity"},
            ),
            (
                ["-H", "--host"],
                {
                    "type": str,
                    "required": True,
                    "metavar": "",
                    "help": "server IP address",
                },
            ),
            (
                ["-p", "--port"],
                {"type": int, "metavar": "", "help": "server port"},
            ),
            (
                ["-r", "--protocol"],
                {
                    "type": str,
                    "default": "GBN",
                    "metavar": "",
                    "help": "error recovery protocol",
                },
            ),
            (
                ["--log-file"],
                {
                    "type": str,
                    "default": "",
                    "help": "log file path",
                },
            ),
        ]

        if self.include_storage:
            common_args.append(
                (
                    ["-s", "--storage"],
                    {
                        "type": str,
                        "required": True,
                        "metavar": "",
                        "help": "storage dir path",
                    },
                )
            )
        if self.include_destination:
            common_args.append(
                (
                    ["-d", "--dst"],
                    {
                        "type": str,
                        "required": True,
                        "metavar": "",
                        "help": "destination file path",
                    },
                )
            )
        if self.include_filename:
            common_args.append(
                (
                    ["-n", "--name"],
                    {
                        "type": str,
                        "required": True,
                        "metavar": "",
                        "help": "file name",
                    },
                )
            )

        for flags, options in common_args:
            self.parser.add_argument(*flags, **options)

    def get_arguments(self) -> argparse.Namespace:
        return self.parser.parse_args()
