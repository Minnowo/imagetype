from .base import FileType
from . import bytereader as br


class IsoBmff(FileType):
    """
    Implements the ISO-BMFF base type.
    """

    def __init__(self, mime, extension):
        super(IsoBmff, self).__init__(mime=mime, extension=extension)

    def _is_isobmff(self, buf):
        if len(buf) < 16 or buf[4:8] != b"ftyp":
            return False

        return not len(buf) < int.from_bytes(buf[0:4], byteorder="big")

    def _get_ftyp(self, buf: bytearray):

        ftyp_len = int.from_bytes(buf[0:4], byteorder="big")

        major_brand = buf[8:12].decode(errors="ignore")

        minor_version = int.from_bytes(buf[12:16], byteorder="big")

        compatible_brands = (
            buf[i : i + 4].decode(errors="ignore") for i in range(16, ftyp_len, 4)
        )

        return major_brand, minor_version, compatible_brands

    def get_size(self, buf: bytearray):

        if not self._is_isobmff(buf):
            return (0, 0)

        # yeah this is questionable, but at least it works
        # cause i'm really struggling to find anything for isobmff online
        # but i do know there's a ispe box that looks like:
        # | size (20) | type (ispe) | version | flags  | width  | height
        # | 4 byte    | 4 byte      | 1 byte  | 3 byte | 4 byte | 4 byte

        # we can skip first 16 bytes here because we know the minor version is 12:16
        offset = buf.find(b"ispe", 16)

        if offset == -1 or offset + 16 >= len(buf):
            return (0, 0)

        return br.read_int(buf, 4, offset + 8), br.read_int(buf, 4, offset + 12)
