from typing import BinaryIO


def read_bytes(buf: bytearray, length: int, offset: int = 0):

    return buf[offset : offset + length]


def read_int(
    buf: bytearray,
    length: int,
    offset: int = 0,
    byteorder: str = "big",
    signed=False,
):

    return int.from_bytes(read_bytes(buf, length, offset), byteorder, signed=signed)


def read_str(buf: bytearray, length: int, offset: int = 0):

    return read_bytes(buf, length, offset).decode("utf-8", errors="ignore")


def buffer_read_int(buffer: BinaryIO, length: int, byteorder="big", signed=False):
    return int.from_bytes(buffer.read(length), byteorder=byteorder, signed=signed)


def buffer_read_str(buffer: BinaryIO, length: int):

    return buffer.read(length).decode("utf-8", errors="ignore")
