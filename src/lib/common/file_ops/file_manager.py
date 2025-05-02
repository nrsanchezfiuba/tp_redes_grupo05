import os
from enum import Enum


class FileOperation(Enum):
    READ = "rb"
    WRITE = "wb"


BLOCK_SIZE = 1000


class FileManager:
    def __init__(self, dir_path: str, file_name: str, mode: FileOperation) -> None:
        self.mode = mode
        self.filepath = self._validate_file(dir_path, file_name)
        os.makedirs(dir_path, exist_ok=True)
        self.file = open(self.filepath, mode.value)

    def __exit__(self) -> None:
        if self.file:
            self.file.close()

    def read_chunk(self) -> bytes:
        return self.file.read(BLOCK_SIZE)

    def write_chunk(self, content: bytes) -> None:
        self.file.write(content)
        self.file.flush()

    def _validate_file(self, dir_path: str, file_name: str) -> str:
        filepath = os.path.join(dir_path, file_name)
        if not os.path.exists(filepath) and self.mode == FileOperation.READ:
            raise FileNotFoundError(f"File {file_name} not found in {dir_path}.")
        return filepath
