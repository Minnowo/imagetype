from .isobmff import IsoBmff
from .base import FileType


class Jpeg(FileType):
    """
    Implements the JPEG image type matcher.
    """

    MIME = "image/jpeg"
    EXTENSION = "jpg"
    EXTENSION_ALTERNATE = ["jpeg", "jfif", "jpe", "jif", "jfi"]

    def __init__(self):
        super(Jpeg, self).__init__(
            mime=self.MIME,
            extension=self.EXTENSION,
            extension_alternate=self.EXTENSION_ALTERNATE,
        )

    def match(self, buf: bytearray):
        return len(buf) > 2 and buf[0] == 0xFF and buf[1] == 0xD8 and buf[2] == 0xFF

    def get_size(self, buf: bytearray):

        if not self.match(buf):
            return (0, 0)

        length = len(buf)

        i = 2

        while i + 8 < length and buf[i] == 0xFF:

            marker = buf[i + 1]
            chunk_length = int.from_bytes(
                [buf[i + 2], buf[i + 3]], byteorder="big", signed=True
            )

            i += 4

            if marker == 0xC0 or marker == 0xC2:

                # make sure to read height before width
                height = int.from_bytes([buf[i + 1], buf[i + 2]], byteorder="big")
                width = int.from_bytes([buf[i + 3], buf[i + 4]], byteorder="big")

                return (width, height)

            if chunk_length < 0:

                # since chunk_length is a signed int16
                # we convert to a unsigned int16
                unsigned_chunk_length = chunk_length + 65536  # 1 << 16

                i += unsigned_chunk_length - 2

            else:
                i += chunk_length - 2

        return (0, 0)


class Jpx(FileType):
    """
    Implements the JPEG2000 image type matcher.
    """

    MIME = "image/jpx"
    EXTENSION = "jpx"

    def __init__(self):
        super(Jpx, self).__init__(mime=self.MIME, extension=self.EXTENSION)

    def match(self, buf: bytearray):
        return (
            len(buf) > 50
            and buf[0] == 0x00
            and buf[1] == 0x00
            and buf[2] == 0x00
            and buf[3] == 0x0C
            and buf[16:24] == b"ftypjp2 "
        )


class Png(FileType):
    """
    Implements the PNG image type matcher.
    """

    MIME = "image/png"
    EXTENSION = "png"

    def __init__(self):
        super(Png, self).__init__(mime=Png.MIME, extension=Png.EXTENSION)

    def match(self, buf: bytearray):
        return (
            len(buf) > 7
            and buf[0] == 0x89
            and buf[1] == 0x50
            and buf[2] == 0x4E
            and buf[3] == 0x47
            and buf[4] == 0x0D
            and buf[5] == 0x0A
            and buf[6] == 0x1A
            and buf[7] == 0x0A
        )

    def get_size(self, buf: bytearray):

        if not self.match(buf) or len(buf) < 24:
            return (0, 0)

        return (
            int.from_bytes([buf[16], buf[17], buf[18], buf[19]], byteorder="big"),
            int.from_bytes([buf[20], buf[21], buf[22], buf[23]], byteorder="big"),
        )


class Apng(Png):
    """
    Implements the APNG image type matcher.
    """

    MIME = "image/apng"
    EXTENSION = "apng"
    EXTENSION_ALTERNATE = ["png"]

    def __init__(self):
        super(Png, self).__init__(
            mime=self.MIME,
            extension=self.EXTENSION,
            extension_alternate=self.EXTENSION_ALTERNATE,
        )

    def match(self, buf: bytearray):

        # png magick bytes check
        if not super().match(buf):
            return False

        # cursor in buf, skip already readed 8 bytes
        i = 8
        while len(buf) > i:
            data_length = int.from_bytes(buf[i : i + 4], byteorder="big")
            i += 4

            chunk_type = buf[i : i + 4].decode("ascii", errors="ignore")
            i += 4

            # acTL chunk in APNG should appears first than IDAT
            # IEND is end of PNG
            if chunk_type == "IDAT" or chunk_type == "IEND":
                return False
            elif chunk_type == "acTL":
                return True

            # move to the next chunk by skipping data and crc (4 bytes)
            i += data_length + 4

        return False


class Gif(FileType):
    """
    Implements the GIF image type matcher.
    """

    MIME = "image/gif"
    EXTENSION = "gif"

    def __init__(self):
        super(Gif, self).__init__(
            mime=Gif.MIME,
            extension=Gif.EXTENSION,
        )

    def match(self, buf: bytearray):
        return (
            len(buf) > 5
            and buf[0] == 0x47
            and buf[1] == 0x49
            and buf[2] == 0x46
            and buf[3] == 0x38
            and (buf[4] in (0x39, 0x37))
            and buf[5] == 0x61
        )

    def get_size(self, buf: bytearray):

        if not self.match(buf):
            return (0, 0)

        return (
            int.from_bytes([buf[6], buf[7]], byteorder="little"),
            int.from_bytes([buf[8], buf[9]], byteorder="little"),
        )


class Webp(FileType):
    """
    Implements the WEBP image type matcher.
    """

    MIME = "image/webp"
    EXTENSION = "webp"

    TYPE_INVALID_UNKNOWN = -1
    TYPE_LOSSY = 0
    TYPE_LOESSLESS = 1
    TYPE_EXTENDED = 2

    def __init__(self):
        super(Webp, self).__init__(
            mime=self.MIME,
            extension=self.EXTENSION,
        )

    def match(self, buf: bytearray):
        return (
            len(buf) > 15
            # RIFF
            and buf[0] == 0x52
            and buf[1] == 0x49
            and buf[2] == 0x46
            and buf[3] == 0x46
            # WEBP
            and buf[8] == 0x57
            and buf[9] == 0x45
            and buf[10] == 0x42
            and buf[11] == 0x50
            # VP8
            and buf[12] == 0x56
            and buf[13] == 0x50
            and buf[14] == 0x38
            # ' ' or 'L' or 'X'
            and (buf[15] in (0x20, 0x4C, 0x58))
        )

    def get_type(self, buf: bytearray):

        if not self.match(buf):
            return self.TYPE_INVALID_UNKNOWN

        if buf[15] == 0x20:
            return self.TYPE_LOSSY

        if buf[15] == 0x4C:
            return self.TYPE_LOESSLESS

        if buf[15] == 0x58:
            return self.TYPE_EXTENDED

    def get_size(self, buf: bytearray):

        # https://developers.google.com/speed/webp/docs/riff_container
        # https://datatracker.ietf.org/doc/html/rfc6386
        # https://wiki.tcl-lang.org/page/Reading+WEBP+image+dimensions

        webp_type = self.get_type(buf)

        if webp_type == self.TYPE_INVALID_UNKNOWN:
            return (0, 0)

        if webp_type == self.TYPE_LOSSY:

            # must read at least 30 bytes, and 3 byte sig
            if len(buf) < 30 or buf[23] != 0x9D or buf[24] != 0x1 or buf[25] != 0x2A:
                return (0, 0)

            return (
                int.from_bytes([buf[26], buf[27]], byteorder="little"),
                int.from_bytes([buf[28], buf[29]], byteorder="little"),
            )

        # # lossless webp
        if webp_type == self.TYPE_LOESSLESS:

            # must read at least 25 bytes, and 1 byte sig
            if len(buf) < 25 or buf[20] != 0x2F:
                return (0, 0)

            return (
                1 + (((buf[22] & 63) << 8) | buf[21]),
                1 + (((buf[24] & 15) << 10) | (buf[23] << 2) | ((buf[22] & 192) >> 6)),
            )

        # # extended webp
        if webp_type == self.TYPE_EXTENDED:

            # must read at least 30 bytes
            if len(buf) < 30:
                return (0, 0)

            return (
                1 + int.from_bytes([buf[24], buf[25], buf[26]], byteorder="little"),
                1 + int.from_bytes([buf[27], buf[28], buf[29]], byteorder="little"),
            )

        return (0, 0)


class Tiff(FileType):
    """
    Implements the TIFF image type matcher.
    """

    MIME = "image/tiff"
    EXTENSION = "tif"

    TYPE_TIFF_INVALID_UNKNOWN = -1
    TYPE_TIFF_LITTLE_ENDIAN = 0
    TYPE_TIFF_BIG_ENDIAN = 1

    def __init__(self):
        super(Tiff, self).__init__(
            mime=self.MIME,
            extension=self.EXTENSION,
        )

    def match(self, buf: bytearray):
        return (
            len(buf) > 9
            and (
                (buf[0] == 0x49 and buf[1] == 0x49 and buf[2] == 0x2A and buf[3] == 0x0)
                or (
                    buf[0] == 0x4D
                    and buf[1] == 0x4D
                    and buf[2] == 0x0
                    and buf[3] == 0x2A
                )
            )
            and not (buf[8] == 0x43 and buf[9] == 0x52)
        )

    def get_type(self, buf: bytearray):

        if not self.match(buf):
            return self.TYPE_TIFF_INVALID_UNKNOWN

        if buf[0] == 0x4D and buf[1] == 0x4D and buf[2] == 0x0 and buf[3] == 0x2A:
            return self.TYPE_TIFF_BIG_ENDIAN

        if buf[0] == 0x49 and buf[1] == 0x49 and buf[2] == 0x2A and buf[3] == 0x0:
            return self.TYPE_TIFF_LITTLE_ENDIAN

    def get_size(self, buf: bytearray):

        # https://www.awaresystems.be/imaging/tiff/tifftags/baseline.html

        tiff_type = self.get_type(buf)

        if tiff_type == self.TYPE_TIFF_INVALID_UNKNOWN:
            return (0, 0)

        endian = "little"

        if tiff_type == self.TYPE_TIFF_BIG_ENDIAN:
            endian = "big"

        length = len(buf)

        idf_start = int.from_bytes([buf[4], buf[5], buf[6], buf[7]], byteorder=endian)

        i = idf_start

        if i >= length:
            return (0, 0)

        number_of_idf = int.from_bytes([buf[i], buf[i + 1]], byteorder=endian)

        i += 2

        width = 0
        height = 0

        for _ in range(number_of_idf):

            if i + 12 > length:
                return (width, height)

            field = int.from_bytes([buf[i], buf[i + 1]], byteorder=endian)

            i += 2

            if field == 256:
                width = int.from_bytes(
                    [buf[i + 6], buf[i + 7], buf[i + 8], buf[i + 9]], byteorder=endian
                )

            elif field == 257:
                height = int.from_bytes(
                    [buf[i + 6], buf[i + 7], buf[i + 8], buf[i + 9]], byteorder=endian
                )

            i += 10

            if width > 0 and height > 0:

                return (width, height)

        return (width, height)


class Bmp(FileType):
    """
    Implements the BMP image type matcher.
    """

    MIME = "image/bmp"
    EXTENSION = "bmp"

    def __init__(self):
        super(Bmp, self).__init__(
            mime=self.MIME,
            extension=self.EXTENSION,
        )

    def match(self, buf: bytearray):
        return len(buf) > 1 and buf[0] == 0x42 and buf[1] == 0x4D

    def get_size(self, buf: bytearray):

        if not self.match(buf) or len(buf) < 26:
            return (0, 0)

        return (
            int.from_bytes([buf[18], buf[19], buf[20], buf[21]], byteorder="little"),
            int.from_bytes([buf[22], buf[23], buf[24], buf[25]], byteorder="little"),
        )


class Jxr(FileType):
    """
    Implements the JXR image type matcher.
    """

    MIME = "image/vnd.ms-photo"
    EXTENSION = "jxr"

    def __init__(self):
        super(Jxr, self).__init__(
            mime=self.MIME,
            extension=self.EXTENSION,
        )

    def match(self, buf: bytearray):
        return len(buf) > 2 and buf[0] == 0x49 and buf[1] == 0x49 and buf[2] == 0xBC


class Psd(FileType):
    """
    Implements the PSD image type matcher.
    """

    MIME = "image/vnd.adobe.photoshop"
    EXTENSION = "psd"

    def __init__(self):
        super(Psd, self).__init__(
            mime=self.MIME,
            extension=self.EXTENSION,
        )

    def match(self, buf: bytearray):
        return (
            len(buf) > 3
            and buf[0] == 0x38
            and buf[1] == 0x42
            and buf[2] == 0x50
            and buf[3] == 0x53
        )

    def get_size(self, buf: bytearray):

        if not self.match(buf) or len(buf) < 22:
            return (0, 0)

        height = (
            int.from_bytes([buf[14], buf[15], buf[16], buf[17]], byteorder="big"),
        )
        width = (int.from_bytes([buf[18], buf[19], buf[20], buf[21]], byteorder="big"),)

        return (width, height)


class Ico(FileType):
    """
    Implements the ICO image type matcher.
    """

    MIME = "image/x-icon"
    EXTENSION = "ico"

    def __init__(self):
        super(Ico, self).__init__(
            mime=self.MIME,
            extension=self.EXTENSION,
        )

    def match(self, buf: bytearray):
        return (
            len(buf) > 3
            and buf[0] == 0x00
            and buf[1] == 0x00
            and buf[2] == 0x01
            and buf[3] == 0x00
        )

    def get_sizes(self, buf: bytearray):

        if not self.match(buf) or len(buf) < 6:
            return (0, 0)

        number_of_images = int.from_bytes([buf[4], buf[5]], byteorder="little")

        sizes = []

        length = len(buf)

        i = 6

        for _ in range(number_of_images):

            if i + 2 > length:
                return sizes

            width = 256
            height = 256

            if buf[i] != 0:
                width = buf[i]

            if buf[i + 1] != 0:
                height = buf[i + 1]

            # if buf[i + 3] != 0:  # reserved should be 0
            #     raise "invalid image??"

            # color_planes = int.from_bytes(buf[4:2], byteorder="little")

            # if color_planes != 0 and color_planes != 1: # should be 0 or 1
            #     raise "invalid image"

            sizes.append((width, height))

            i += 16
            # image_data_size   = int.from_bytes(io_byte_reader.read(4), byteorder="little")
            # image_data_offset = int.from_bytes(io_byte_reader.read(4), byteorder="little")

        return sizes

    def get_size(self, buf: bytearray):

        sizes = self.get_sizes(buf)

        if len(sizes) == 0:
            return (0, 0)

        return sizes[0]


class Heic(IsoBmff):
    """
    Implements the HEIC image type matcher.
    """

    MIME = "image/heic"
    EXTENSION = "heic"

    def __init__(self):
        super(Heic, self).__init__(mime=self.MIME, extension=self.EXTENSION)

    def match(self, buf: bytearray):
        if not self._is_isobmff(buf):
            return False

        major_brand, minor_version, compatible_brands = self._get_ftyp(buf)
        if major_brand == "heic":
            return True
        if major_brand in ["mif1", "msf1"] and "heic" in compatible_brands:
            return True
        return False


class Avif(IsoBmff):
    """
    Implements the AVIF image type matcher.
    """

    MIME = "image/avif"
    EXTENSION = "avif"

    def __init__(self):
        super(Avif, self).__init__(mime=self.MIME, extension=self.EXTENSION)

    def match(self, buf: bytearray):
        if not self._is_isobmff(buf):
            return False

        major_brand, minor_version, compatible_brands = self._get_ftyp(buf)
        if major_brand == "avif":
            return True
        if major_brand in ["mif1", "msf1"] and "avif" in compatible_brands:
            return True
        return False


class Dcm(FileType):

    MIME = "application/dicom"
    EXTENSION = "dcm"
    OFFSET = 128

    def __init__(self):
        super(Dcm, self).__init__(mime=self.MIME, extension=self.EXTENSION)

    def match(self, buf: bytearray):
        return (
            len(buf) > Dcm.OFFSET + 4
            and buf[Dcm.OFFSET + 0] == 0x44
            and buf[Dcm.OFFSET + 1] == 0x49
            and buf[Dcm.OFFSET + 2] == 0x43
            and buf[Dcm.OFFSET + 3] == 0x4D
        )


class Dwg(FileType):
    """Implements the Dwg image type matcher."""

    MIME = "image/vnd.dwg"
    EXTENSION = "dwg"

    def __init__(self):
        super(Dwg, self).__init__(mime=self.MIME, extension=self.EXTENSION)

    def match(self, buf: bytearray):
        return buf[:4] == bytearray([0x41, 0x43, 0x31, 0x30])


class Xcf(FileType):
    """Implements the Xcf image type matcher."""

    MIME = "image/x-xcf"
    EXTENSION = "xcf"

    def __init__(self):
        super(Xcf, self).__init__(mime=self.MIME, extension=self.EXTENSION)

    def match(self, buf: bytearray):
        return buf[:10] == bytearray(
            [0x67, 0x69, 0x6D, 0x70, 0x20, 0x78, 0x63, 0x66, 0x20, 0x76]
        )


class Cr2(FileType):
    """
    Implements the CR2 image type matcher.
    """

    MIME = "image/x-canon-cr2"
    EXTENSION = "cr2"

    def __init__(self):
        super(Cr2, self).__init__(
            mime=self.MIME,
            extension=self.EXTENSION,
        )

    def match(self, buf: bytearray):
        return (
            len(buf) > 9
            and (
                (buf[0] == 0x49 and buf[1] == 0x49 and buf[2] == 0x2A and buf[3] == 0x0)
                or (
                    buf[0] == 0x4D
                    and buf[1] == 0x4D
                    and buf[2] == 0x0
                    and buf[3] == 0x2A
                )
            )
            and buf[8] == 0x43
            and buf[9] == 0x52
        )
