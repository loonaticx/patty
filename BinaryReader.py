import struct
from typing import Any


class BinaryReader:
    def __init__(self, data: bytes, pos: int = 0):
        self.__data = bytes(data)
        self.__pos = pos

    def unpack(self, format: str) -> tuple[Any, ...]:
        size = struct.calcsize(format)
        data = self.read(size)
        return struct.unpack(format, data)

    def read(self, length: int) -> bytes:
        data = self.__data[self.__pos:self.__pos + length]
        if len(data) != length:
            raise EOFError("read %d but expected %d" % (len(data), length))

        self.__pos += length
        return data

    def remaining(self):
        return self.__data[self.__pos:]
