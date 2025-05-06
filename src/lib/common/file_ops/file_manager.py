import os
from typing import Any
import aiofiles
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
        self.file: Any = None

    async def open(self):
        self.file = await aiofiles.open(self.filepath, mode=self.mode.value)
        return self

    async def close(self):
        if self.file:
            await self.file.close()

    async def read_chunk(self) -> bytes:
        if self.file is None:
            raise ValueError("File is not opened for reading.")
        return await self.file.read(BLOCK_SIZE)

    async def write_chunk(self, content: bytes) -> None:
        if self.file is None:
            raise ValueError("File is not opened for writing.")
        await self.file.write(content)
        await self.file.flush()

    def _validate_file(self, dir_path: str, file_name: str) -> str:
        filepath = os.path.join(dir_path, file_name)
        if not os.path.exists(filepath) and self.mode == FileOperation.READ:
            raise FileNotFoundError(f"File {file_name} not found in {dir_path}.")
        return filepath
