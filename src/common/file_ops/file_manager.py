import os
from enum import Enum


class FileOperation(Enum):
    READ = "rb"
    WRITE = "wb"


class FileManager:
    def __init__(self, dir_path: str, file_name: str, mode: FileOperation) -> None:
        self.mode = mode
        self.filepath = self._validate_file(dir_path, file_name)
        os.makedirs(self.filepath, exist_ok=True)
        self.file = open(self.filepath, mode.value)

    # def __del__(self) -> None:
    #     if self.file:
    #         self.file.close()

    def read_file(self, block_size: int) -> bytes:
        return self.file.read(block_size)

    def write_file(self, content: bytes) -> None:
        self.file.write(content)
        self.file.flush()

    def _validate_file(self, dir_path: str, file_name: str) -> str:
        """Validate and return full file path."""
        filepath = os.path.join(dir_path, file_name)
        if not os.path.exists(dir_path) and self.mode == FileOperation.READ:
            raise FileNotFoundError(f"File {file_name} not found in {dir_path}.")
        elif os.path.exists(dir_path) and self.mode == FileOperation.WRITE:
            raise FileExistsError(f"File {file_name} already exists in {dir_path}.")
        return filepath
