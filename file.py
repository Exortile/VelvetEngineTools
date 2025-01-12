from struct import pack
from typing import BinaryIO

from .structures import *
from .util import *


class BigEndianFileWriter:
    _file: BinaryIO

    def __init__(self, file: BinaryIO):
        self._file = file

    def __enter__(self):
        return self

    def __exit__(self, _, __, ___):
        self._file.close()

    def __getattr__(self, attribute):
        return getattr(self._file, attribute)

    def write_u8(self, val):
        self._file.write(pack(">B", val))

    def write_u16(self, val):
        self._file.write(pack(">H", val))

    def write_u32(self, val):
        self._file.write(pack(">I", val))

    def write_s8(self, val):
        self._file.write(pack(">b", val))

    def write_s16(self, val):
        self._file.write(pack(">h", val))

    def write_s32(self, val):
        self._file.write(pack(">i", val))

    def write_f32(self, val):
        self._file.write(pack(">f", val))

    def write_f64(self, val):
        self._file.write(pack(">d", val))

    def align(self, bits=16):
        while self._file.tell() & (bits - 1):
            self._file.write(b'\x00')


class VelvetFileWriter(BigEndianFileWriter):
    def write_header_only(self, header_id: str):
        header_id_bytes = bytes(header_id.upper(), "ascii")
        header = VHeader(header_id_bytes)
        self._file.write(header)

    def write_section(self, header_id: str, *data) -> int:
        """
        Writes a section to the file with the given ID and data.
        Returns the absolute offset to the start of the written data (header excluded).
        """

        start_offset = self._file.tell()
        header_id_bytes = bytes(header_id.upper(), "ascii")

        unaligned_data_len = sum([len(d) for d in data])
        data_len = align(unaligned_data_len, 16)
        next_offset = sizeof(VHeader) + data_len
        header = VHeader(header_id_bytes, start_offset + next_offset)

        self._file.write(header)

        for d in data:
            self._file.write(d)

        self.align()

        return start_offset + sizeof(VHeader)

    def write_data_section(self, data):
        return self.write_section("VDAT", data)

    def write_end(self):
        header = VHeader(b"VEND")
        self._file.write(header)
        self.align(32)
