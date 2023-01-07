# -*- coding: utf-8 -*-
import re, os
from typing import BinaryIO

from .. import bytereader as br

ZERO_OR_ONE = 0
EXACTLY_ONE = 1
ONE_OR_MORE = 2
ANY_NUMBER = 3


def read_string(file: BinaryIO, length: int = None):

    if length:
        return file.read(length).decode()

    return "".join(iter(lambda: file.read(1).decode("ascii"), "\x00"))


def indent(rep):
    return re.sub(r"^", "  ", rep, flags=re.M)


def read_box(file: BinaryIO):

    size = br.buffer_read_int(file, 4)

    box_type = read_string(file, 4)

    box_class = CLASS_MAP.get(box_type, None)

    if box_class is None:
        return None

    box: Box = box_class.__new__(box_class)

    if isinstance(box, FullBox):
        version = br.buffer_read_int(file, 1)
        flags = br.buffer_read_int(file, 3)
        box.__init__(size=size, version=version, flags=flags)

    else:
        box.__init__(size=size)

    if box.get_box_size():
        box.read(file)

    return box


class Box(object):
    box_type = None

    def __init__(self, size=None):
        self.size = size
        self.subboxes = {}
        self.raw = b""

    def get_box_size(self):
        """get box size excluding header"""
        return self.size - 8

    def read(self, reader: BinaryIO):

        read_size = self.get_box_size()

        while read_size > 0:

            box: Box = read_box(reader)

            if not box:
                break

            self.subboxes[box.box_type] = box

            read_size -= box.size


class FullBox(Box):
    box_type = None

    def __init__(self, size, version=None, flags=None):
        super().__init__(size)
        self.version = version
        self.flags = flags

    def get_box_size(self):
        """get box size excluding header"""
        return self.size - 12


### ccst start ###


class ccst(Box):
    box_type = "ccst"
    is_mandatory = False

    def read(self, reader: BinaryIO):

        self.raw = reader.read(self.get_box_size())


### ccst end ###


### dinf start ###


class DataInformationBox(Box):
    box_type = "dinf"
    is_mandatry = True
    quantity = EXACTLY_ONE


class DataReferenceBox(FullBox):
    box_type = "dref"
    is_mandatry = True
    quantity = EXACTLY_ONE

    def __init__(self, size, version, flags):
        super().__init__(size=size, version=version, flags=flags)
        self.data_entry = []

    def read(self, reader: BinaryIO):

        entry_count = br.buffer_read_int(reader, 4)

        for _ in range(entry_count):

            box = read_box(reader)

            if not box:
                break

            self.data_entry.append(box)


class DataEntryUrlBox(FullBox):
    box_type = "url "
    is_mandatry = True

    def __init__(self, size, version, flags):
        super().__init__(size=size, version=version, flags=flags)
        self.location = None

    def read(self, reader: BinaryIO):
        self.location = read_string(reader)


class DataEntryUrnBox(FullBox):
    box_type = "urn "
    is_mandatry = True

    def __init__(self, size, version, flags):
        super().__init__(size=size, version=version, flags=flags)
        self.name = None
        self.location = None

    def read(self, reader: BinaryIO):
        self.name = read_string(reader)
        self.location = read_string(reader)


### dinf end ###


### ftyp start ###


class FileTypeBox(Box):
    box_type = "ftyp"
    is_mandatory = True
    quantity = EXACTLY_ONE

    def __init__(self, size):
        super().__init__(size=size)
        self.majar_brand = None
        self.minor_version = None
        self.compatible_brands = []

    def __repr__(self):
        return f"<{self.__class__.__name__}, major: {self.majar_brand}, minor: {self.minor_version}, compatible: {self.compatible_brands}>"

    def read(self, reader: BinaryIO):

        self.majar_brand = read_string(reader, 4)

        self.minor_version = br.buffer_read_int(reader, 4)

        num_compatible_brands = int((self.size - 16) / 4)

        for _ in range(num_compatible_brands):
            compat_brand = read_string(reader, 4)
            self.compatible_brands.append(compat_brand)


### ftyp end ###


### hdlr start ###


class HandlerReferenceBox(FullBox):
    box_type = "hdlr"
    is_mandatory = True
    quantity = EXACTLY_ONE

    def __init__(self, size, version, flags):
        super().__init__(size=size, version=version, flags=flags)
        self.pre_defined = None
        self.handler_type = None
        self.reserved = []
        self.name = None

    def __repr__(self):
        return f"<{self.__class__.__name__}, name: {self.name}, handlerType: {self.handler_type}>"

    def read(self, reader: BinaryIO):
        self.pre_defined = br.buffer_read_int(reader, 4)
        self.handler_type = read_string(reader, 4)
        for _ in range(3):  # 3*4=12bytes
            self.reserved.append(br.buffer_read_int(reader, 4))
        self.name = read_string(reader)


### hdlr end ###


### iinf start ###


class ItemInformationBox(FullBox):
    box_type = "iinf"
    is_mandatory = False

    def __init__(self, size, version, flags):
        super().__init__(size=size, version=version, flags=flags)
        self.item_infos = []

    def __repr__(self):
        return f"""<{self.__class__.__name__}, count: {len(self.item_infos)}, items: {self.item_infos}>"""

    def read(self, reader: BinaryIO):
        count_size = 2 if self.version == 0 else 4
        entry_count = br.buffer_read_int(reader, count_size)

        for _ in range(entry_count):
            box = read_box(reader)
            if not box:
                break
            if box.box_type == "infe":
                self.item_infos.append(box)


class ItemInfomationEntry(FullBox):
    box_type = "infe"

    def __init__(self, size, version, flags):
        super().__init__(size=size, version=version, flags=flags)
        self.item_id = None
        self.item_protection_index = None
        self.item_name = None
        self.item_extension = None
        self.item_type = None
        self.content_type = None
        self.content_encoding = None
        self.uri_type = None

    def __repr__(self):

        rep = ""

        if self.version >= 2:
            rep = f", type: {self.item_type}"

        return f"<{self.__class__.__name__}, ID: {self.item_id}, protectionIndex: {self.item_protection_index}, name: {self.item_name}{rep}>"

    def read(self, reader: BinaryIO):
        if self.version == 0 or self.version == 1:
            self.item_id = br.buffer_read_int(reader, 2)
            self.item_protection_index = br.buffer_read_int(reader, 2)
            self.item_name = read_string(reader)
            self.content_type = read_string(reader)
            self.content_encoding = read_string(reader)

            if self.version == 1:
                extension_type = read_string(reader, 4)
                fdel = FDItemInfoExtension()
                fdel.read(reader)
                self.item_extension = fdel
        elif self.version >= 2:
            if self.version == 2:
                self.item_id = br.buffer_read_int(reader, 2)
            elif self.version == 3:
                self.item_id = br.buffer_read_int(reader, 4)
            self.item_protection_index = br.buffer_read_int(reader, 2)
            self.item_type = read_string(reader, 4)
            self.item_name = read_string(reader)

            if self.item_type == "mime":
                self.content_type = read_string(reader)
                self.content_encoding = read_string(reader)
            elif self.item_type == "uri ":
                self.uri_type = read_string(reader)


class FDItemInfoExtension(object):
    def __init__(self):
        self.content_location = None
        self.content_md5 = None
        self.content_length = None
        self.transfer_length = None
        self.group_ids = []

    def read(self, reader: BinaryIO):
        """read"""
        self.content_location = read_string(reader)
        self.content_md5 = read_string(reader)
        self.content_length = br.buffer_read_int(reader, 8)
        self.transfer_length = br.buffer_read_int(reader, 8)
        entry_count = br.buffer_read_int(reader, 1)
        for _ in range(entry_count):
            group_id = br.buffer_read_int(reader, 4)
            self.group_ids.append(group_id)


### iinf end ###


### iloc start ###


class ItemLocationBox(FullBox):
    box_type = "iloc"
    is_mandatory = False

    def __init__(self, size, version, flags):
        super().__init__(size=size, version=version, flags=flags)
        self.offset_size = None
        self.length_size = None
        self.base_offset_size = None
        self.reserved = None
        self.items = []

    def __repr__(self):
        return f"<{self.__class__.__name__}, offset: {self.offset_size}, length: {self.length_size}>"

    def read(self, reader: BinaryIO):
        byte = br.buffer_read_int(reader, 1)
        self.offset_size = (byte >> 4) & 0b1111
        self.length_size = byte & 0b1111
        byte = br.buffer_read_int(reader, 1)
        self.base_offset_size = (byte >> 4) & 0b1111
        self.reserved = byte & 0b1111
        self.items = []
        item_count = br.buffer_read_int(reader, 2)

        for _ in range(item_count):
            item = {}
            item["item_id"] = br.buffer_read_int(reader, 2)
            item["data_reference_index"] = br.buffer_read_int(reader, 2)
            item["base_offset"] = br.buffer_read_int(reader, self.base_offset_size)
            extent_count = br.buffer_read_int(reader, 2)
            item["extents"] = []
            for _ in range(extent_count):
                extent = {}
                extent["extent_offset"] = br.buffer_read_int(reader, self.offset_size)
                extent["extent_length"] = br.buffer_read_int(reader, self.length_size)
                item["extents"].append(extent)
            self.items.append(item)


### iloc end ###


### ipro start ###


class ItemProtectionBox(FullBox):
    box_type = "ipro"
    is_mandatory = False
    quantity = ZERO_OR_ONE

    def __init__(self, size, version, flags):
        super().__init__(size=size, version=version, flags=flags)
        self.protection_informations = []

    def read(self, reader: BinaryIO):
        protection_count = br.buffer_read_int(reader, 2)

        for _ in range(protection_count):
            box = read_box(reader)
            if not box:
                break
            if box.box_type == "sinf":
                self.protection_informations.append(box)


### ipro end ###


### iprp start ###


class ItemPropertiesBox(Box):
    box_type = "iprp"
    is_mandatry = False
    quantity = ZERO_OR_ONE


class ItemPropertyContainer(Box):
    box_type = "ipco"
    is_mandatry = True
    quantity = EXACTLY_ONE


class ImageSpatialExtents(FullBox):
    box_type = "ispe"

    def __init__(self, size, version, flags):
        super().__init__(size=size, version=version, flags=flags)
        self.width = None
        self.height = None

    def read(self, reader: BinaryIO):
        self.width = br.buffer_read_int(reader, 4)
        self.height = br.buffer_read_int(reader, 4)


class PixelAspectRatio(Box):
    box_type = "pasp"

    def read(self, reader: BinaryIO):
        self.raw = reader.read(self.get_box_size())


class ColorInformation(Box):
    box_type = "colr"

    def read(self, reader: BinaryIO):
        self.raw = reader.read(self.get_box_size())


class PixelInformation(Box):
    box_type = "pixi"

    def read(self, reader: BinaryIO):
        self.raw = reader.read(self.get_box_size())


class RelativeInformation(Box):
    box_type = "rloc"

    def read(self, reader: BinaryIO):
        self.raw = reader.read(self.get_box_size())


class ItemPropertyAssociation(FullBox):
    box_type = "ipma"
    is_mandatry = True
    quantity = EXACTLY_ONE

    def __init__(self, size, version, flags):
        super().__init__(size=size, version=version, flags=flags)
        self.items = []

    def read(self, reader: BinaryIO):
        entry_count = br.buffer_read_int(reader, 4)
        id_size = 2 if self.version < 1 else 4
        for _ in range(entry_count):
            item = {}
            item["id"] = br.buffer_read_int(reader, id_size)
            association_count = br.buffer_read_int(reader, 1)
            item["associations"] = []
            for __ in range(association_count):
                association = {}
                if self.flags & 0b1:
                    byte = br.buffer_read_int(reader, 2)
                    association["essential"] = (byte >> 15) & 0b1
                    association["property_index"] = byte & 0b111111111111111
                else:
                    byte = br.buffer_read_int(reader, 1)
                    association["essential"] = (byte >> 7) & 0b1
                    association["property_index"] = byte & 0b1111111
                item["associations"].append(association)
            self.items.append(item)


### iprp end ###


### mdat start ###


class MediaDataBox(Box):
    box_type = "mdat"
    is_mandatory = False

    def __init__(self, size):
        super().__init__(size=size)
        self.data_offset = None

    def read(self, reader: BinaryIO):
        self.data_offset = reader.tell()
        self.raw = reader.read(self.get_box_size())


### mdat end ###


### mdia start ###


class MediaBox(Box):
    box_type = "mdia"
    is_mandatory = True
    quantity = EXACTLY_ONE


class MediaHeaderBox(FullBox):
    box_type = "mdhd"
    is_mandatory = True
    quantity = EXACTLY_ONE

    def __init__(self, size, version, flags):
        super().__init__(size=size, version=version, flags=flags)
        self.creation_time = None
        self.modification_time = None
        self.timescale = None
        self.duration = None
        self.pad = None
        self.language = []  # ISO-639-2/T language code
        self.pre_defined = None

    def read(self, reader: BinaryIO):
        read_size = 8 if self.version == 1 else 4
        self.creation_time = br.buffer_read_int(reader, read_size)
        self.modification_time = br.buffer_read_int(reader, read_size)
        self.timescale = br.buffer_read_int(reader, 4)
        self.duration = br.buffer_read_int(reader, read_size)
        byte = br.buffer_read_int(reader, 2)
        self.pad = (byte >> 15) & 0b1
        self.language.append((byte >> 10) & 0b11111)
        self.language.append((byte >> 5) & 0b11111)
        self.language.append(byte & 0b11111)
        self.pre_defined = br.buffer_read_int(reader, 2)


### mdia end ###


### meta start ###


class MetaBox(FullBox):
    box_type = "meta"
    is_mandatory = False
    quntity = ZERO_OR_ONE


### meta end ###


### minf start ###


class MediaInformationBox(Box):
    box_type = "minf"
    is_mandatory = True
    quantity = EXACTLY_ONE


class VideoMediaHeaderBox(FullBox):
    box_type = "vmhd"
    is_mandatory = True

    def __init__(self, size, version, flags):
        super().__init__(size=size, version=version, flags=flags)
        self.graphicsmode = None
        self.opcolor = []

    def read(self, reader: BinaryIO):
        self.graphicsmode = br.buffer_read_int(reader, 2)
        for _ in range(3):
            self.opcolor.append(br.buffer_read_int(reader, 2))


class SoundMediaHeaderBox(FullBox):
    box_type = "smhd"
    is_mandatory = True

    def __init__(self, size, version, flags):
        super().__init__(size=size, version=version, flags=flags)
        self.balance = None
        self.reserved = None

    def read(self, reader: BinaryIO):
        self.balance = br.buffer_read_int(reader, 2)
        self.reserved = br.buffer_read_int(reader, 2)


class HintMediaHeaderBox(FullBox):
    box_type = "hmhd"
    is_mandatory = True

    def __init__(self, size, version, flags):
        super().__init__(size=size, version=version, flags=flags)
        self.max_pdu_size = None
        self.avg_pdu_size = None
        self.max_bit_rate = None
        self.avg_bit_rate = None
        self.reserved = None

    def read(self, reader: BinaryIO):
        self.max_pdu_size = br.buffer_read_int(reader, 2)
        self.avg_pdu_size = br.buffer_read_int(reader, 2)
        self.max_bit_rate = br.buffer_read_int(reader, 4)
        self.avg_bit_rate = br.buffer_read_int(reader, 4)
        self.reserved = br.buffer_read_int(reader, 4)


class NullMediaHeaderBox(FullBox):
    box_type = "nmhd"
    is_mandatory = True


### minf end ###


### moov start ###


class MovieBox(Box):
    box_type = "moov"
    is_mandatory = True
    quantity = EXACTLY_ONE


class MovieHeaderBox(FullBox):
    box_type = "mvhd"
    is_mandatory = True
    quantity = EXACTLY_ONE

    def __init__(self, size, version, flags):
        super().__init__(size=size, version=version, flags=flags)
        self.creation_time = None
        self.modification_time = None
        self.timescale = None
        self.duration = None
        self.rate = None
        self.volume = None
        self.reserved1 = None
        self.reserved2 = []
        self.matrix = []
        self.pre_defined = []
        self.next_track_id = None

    def read(self, reader: BinaryIO):
        read_size = 8 if self.version == 1 else 4
        self.creation_time = br.buffer_read_int(reader, read_size)
        self.modification_time = br.buffer_read_int(reader, read_size)
        self.timescale = br.buffer_read_int(reader, 4)
        self.duration = br.buffer_read_int(reader, read_size)
        self.rate = br.buffer_read_int(reader, 4)
        self.volume = br.buffer_read_int(reader, 2)
        self.reserved1 = br.buffer_read_int(reader, 2)
        for _ in range(2):
            self.reserved2.append(br.buffer_read_int(reader, 4))
        for _ in range(9):
            self.matrix.append(br.buffer_read_int(reader, 4))
        for _ in range(6):
            self.pre_defined.append(br.buffer_read_int(reader, 4))
        self.next_track_id = br.buffer_read_int(reader, 4)


### moov end ###


### pitm start ###


class PrimaryItemBox(FullBox):
    box_type = "pitm"
    is_mandatory = False

    def read(self, reader: BinaryIO):
        self.item_id = br.buffer_read_int(reader, 2)


### pitm end ###


### sinf start ###


class ProtectionSchemeInfoBox(Box):
    box_type = "sinf"
    is_mandatory = False
    quantity = ONE_OR_MORE


class OriginalFormatBox(Box):
    box_type = "frma"
    is_mandatory = True
    quantity = EXACTLY_ONE

    def __init__(self, size):
        super().__init__(size=size)
        self.data_format = None

    def read(self, reader: BinaryIO):
        self.data_format = br.buffer_read_int(reader, 4)


class SchemeTypeBox(FullBox):
    box_type = "schm"
    is_mandatory = False
    quantity = ZERO_OR_ONE

    def __init__(self, size):
        super().__init__(size=size)
        self.scheme_type = None
        self.scheme_version = None
        self.scheme_uri = None

    def read(self, reader: BinaryIO):
        self.scheme_type = br.buffer_read_int(reader, 4)
        self.scheme_version = br.buffer_read_int(reader, 4)
        if self.flags & 0b1:
            self.scheme_uri = read_string(reader)


class SchemeInformationBox(Box):
    box_type = "schi"
    is_mandatory = False
    quantity = ZERO_OR_ONE


### sinf end ###

### stbl start ###


class SampleTableBox(Box):
    box_type = "stbl"
    is_mandatory = True
    quantity = EXACTLY_ONE


class SampleDescriptionBox(FullBox):
    box_type = "stsd"
    is_mandatory = True
    quantity = EXACTLY_ONE

    def __init__(self, size, version, flags):
        super().__init__(size=size, version=version, flags=flags)
        # self.handler_type = handler_type
        self.samples = []

    def read(self, reader: BinaryIO):
        entry_count = br.buffer_read_int(reader, 4)
        for _ in range(entry_count):
            box = read_box(reader)
            if not box:
                break
            self.samples.append(box)


class SampleEntry(Box):
    def __init__(self, size):
        super().__init__(size=size)
        self.reserveds = []
        self.data_reference_index = None

    def get_box_size(self):
        return super().get_box_size() - 6 + 2

    def read(self, reader: BinaryIO):
        for _ in range(6):
            reserved = br.buffer_read_int(reader, 1)
            self.reserveds.append(reserved)
        self.data_reference_index = br.buffer_read_int(reader, 2)


class HintSampleEntry(SampleEntry):
    """Hint Sample Entry"""

    box_type = "hint"

    def __init__(self, size):
        super().__init__(size=size)

    def read(self, reader: BinaryIO):
        box_size = self.get_box_size()
        self.raw = reader.read(box_size)


class VisualSampleEntry(SampleEntry):
    """Visual Sample Entry"""

    box_type = "vide"

    def __init__(self, size):
        super().__init__(size=size)
        self.pre_defined1 = None
        self.reserved1 = None
        self.pre_defined2 = []
        self.width = None
        self.height = None
        self.horizresolution = None
        self.vertresolution = None
        self.reserved2 = None
        self.frame_count = None
        self.compressorname = None
        self.depth = None
        self.pre_defined3 = None

    def read(self, reader: BinaryIO):
        super().read(reader)
        self.pre_defined1 = br.buffer_read_int(reader, 2)
        self.reserved1 = br.buffer_read_int(reader, 2)
        for _ in range(3):
            self.pre_defined2.append(br.buffer_read_int(reader, 4))
        self.width = br.buffer_read_int(reader, 2)
        self.height = br.buffer_read_int(reader, 2)
        self.horizresolution = br.buffer_read_int(reader, 4)
        self.vertresolution = br.buffer_read_int(reader, 4)
        self.reserved2 = br.buffer_read_int(reader, 4)
        self.frame_count = br.buffer_read_int(reader, 2)
        self.compressorname = read_string(reader, 32)
        self.depth = br.buffer_read_int(reader, 2)
        self.pre_defined3 = br.buffer_read_int(reader, 2)


class AudioSampleEntry(SampleEntry):
    """Audio Sample Entry"""

    box_type = "soun"

    def __init__(self, size):
        super().__init__(size=size)
        self.reserved1 = []
        self.channelcount = None
        self.samplesize = None
        self.pre_defined = None
        self.reserved2 = []
        self.samperate = None

    def read(self, reader: BinaryIO):
        super().read(reader)
        for _ in range(2):
            self.reserved1.append(br.buffer_read_int(reader, 4))
        self.channelcount = br.buffer_read_int(reader, 2)
        self.samplesize = br.buffer_read_int(reader, 2)
        self.pre_defined = br.buffer_read_int(reader, 2)
        for _ in range(2):
            self.reserved2.append(br.buffer_read_int(reader, 2))
        self.samperate = br.buffer_read_int(reader, 4)


class BitRateBox(Box):
    """Bit Rate Box"""

    box_type = "btrt"

    def __init__(self, size):
        super().__init__(size=size)
        self.buffer_size_db = None
        self.max_bitrate = None
        self.avg_bitrate = None

    def read(self, reader: BinaryIO):
        self.buffer_size_db = br.buffer_read_int(reader, 4)
        self.max_bitrate = br.buffer_read_int(reader, 4)
        self.avg_bitrate = br.buffer_read_int(reader, 4)


### sdbl end ###


### stco start ###


class ChunkOffsetBox(FullBox):
    box_type = "stco"
    is_mandatory = True
    quantity = EXACTLY_ONE

    def __init__(self, size, version, flags):
        super().__init__(size=size, version=version, flags=flags)
        self.entries = []

    def read(self, reader: BinaryIO):
        entry_count = br.buffer_read_int(reader, 4)

        for _ in range(entry_count):
            entry = {}
            entry["chunk_offset"] = br.buffer_read_int(reader, 4)
            self.entries.append(entry)


### stco end ###


### stsc start ###


class SampleToChunkBox(FullBox):
    box_type = "stsc"
    is_mandatory = True
    quantity = EXACTLY_ONE

    def __init__(self, size, version, flags):
        super().__init__(size=size, version=version, flags=flags)
        self.entries = []

    def read(self, reader: BinaryIO):
        entry_count = br.buffer_read_int(reader, 4)
        for _ in range(entry_count):
            entry = {}
            entry["first_chunk"] = br.buffer_read_int(reader, 4)
            entry["samples_per_chunk"] = br.buffer_read_int(reader, 4)
            entry["sample_description_index"] = br.buffer_read_int(reader, 4)
            self.entries.append(entry)


### stsc end ###


### stss start ###


class SyncSampleBox(FullBox):
    box_type = "stss"
    is_mandatory = False

    def __init__(self, size, version, flags):
        super().__init__(size=size, version=version, flags=flags)
        self.entries = []

    def read(self, reader: BinaryIO):
        entry_count = br.buffer_read_int(reader, 4)
        for _ in range(entry_count):
            entry = {}
            entry["sample_number"] = br.buffer_read_int(reader, 4)
            self.entries.append(entry)


### stss end ###


### stsz start ###


class SampleSizeBox(FullBox):
    box_type = "stsz"
    is_mandatory = False

    def __init__(self, size, version, flags):
        super().__init__(size=size, version=version, flags=flags)
        self.sample_size = None
        self.entries = []

    def read(self, reader: BinaryIO):
        self.sample_size = br.buffer_read_int(reader, 4)
        sample_count = br.buffer_read_int(reader, 4)

        if self.sample_size == 0:
            for _ in range(sample_count):
                entry = {}
                entry["entry_size"] = br.buffer_read_int(reader, 4)
                self.entries.append(entry)


### stsz end ###


### stts start ###


class TimeToSampleBox(FullBox):
    box_type = "stts"
    is_mandatory = True

    def __init__(self, size, version, flags):
        super().__init__(size=size, version=version, flags=flags)
        self.entry_count = None
        self.entries = []

    def read(self, reader: BinaryIO):
        self.entry_count = br.buffer_read_int(reader, 4)
        for _ in range(self.entry_count):
            entry = {}
            entry["sample_count"] = br.buffer_read_int(reader, 4)
            entry["sample_delta"] = br.buffer_read_int(reader, 4)
            self.entries.append(entry)


### stts end ###


### trak start ###


class TrackBox(Box):
    box_type = "trak"
    is_mandatory = True
    quantity = EXACTLY_ONE


class TrackHeaderBox(FullBox):
    box_type = "tkhd"
    is_mandatory = True
    quantity = EXACTLY_ONE

    def __init__(self, size, version, flags):
        super().__init__(size=size, version=version, flags=flags)
        self.creation_time = None
        self.modification_time = None
        self.track_id = None
        self.duration = None
        self.reserved1 = None
        self.reserved2 = []
        self.layer = None
        self.alternate_group = None
        self.volume = None
        self.reserved3 = None
        self.matrix = []
        self.width = None
        self.height = None

    def read(self, reader: BinaryIO):
        read_size = 8 if self.version == 1 else 4
        self.creation_time = br.buffer_read_int(reader, read_size)
        self.modification_time = br.buffer_read_int(reader, read_size)
        self.track_id = br.buffer_read_int(reader, 4)
        self.reserved1 = br.buffer_read_int(reader, 4)
        self.duration = br.buffer_read_int(reader, read_size)
        for _ in range(2):
            self.reserved2.append(br.buffer_read_int(reader, 4))
        self.layer = br.buffer_read_int(reader, 2)
        self.alternate_group = br.buffer_read_int(reader, 2)
        self.volume = br.buffer_read_int(reader, 2)
        self.reserved3 = br.buffer_read_int(reader, 2)
        for _ in range(9):
            self.matrix.append(br.buffer_read_int(reader, 4))
        self.width = br.buffer_read_int(reader, 4)
        self.height = br.buffer_read_int(reader, 4)


### trak end


### hvc start ###


class HEVCSampleEntry(VisualSampleEntry):
    box_type = "hvc1"
    is_mandatry = True
    quantity = ONE_OR_MORE

    def __init__(self, size):
        super().__init__(size=size)
        self.config = None

    def read(self, reader: BinaryIO):
        super().read(reader)
        self.config = read_box(reader)


class HEVCConfigurationBox(Box):
    box_type = "hvcC"

    def __init__(self, size):
        super().__init__(size=size)
        self.hevc_config = None

    def read(self, reader: BinaryIO):
        self.hevc_config = HEVCDecoderConfigurationRecord()
        self.hevc_config.read(reader)


class HEVCDecoderConfigurationRecord(object):
    def __init__(self):
        self.configuration_version = None  # 8
        self.general_profile_space = None  # 2
        self.general_tier_flag = None  # 1
        self.general_profile_idc = None  # 5
        self.general_profile_compat_flags = None  # 32
        self.general_const_indicator_flags = None  # 48
        self.general_level_idc = None  # 8
        self.reserved1 = 0b1111
        self.min_spatial_segmentation_idc = None  # 12
        self.reserved2 = 0b111111
        self.parallelism_type = None  # 2
        self.reserved3 = 0b111111
        self.chroma_format = None  # 2
        self.reserved4 = 0b11111
        self.bit_depth_luma_minus_8 = None  # 3
        self.reserved5 = 0b11111
        self.bit_depth_chroma_minus_8 = None  # 3
        self.avg_frame_rate = None  # 16
        self.constant_frame_rate = None  # 2
        self.num_temporal_layers = None  # 3
        self.temporal_id_nested = None  # 1
        self.length_size_minus_1 = None  # 2
        self.num_of_arrays = None  # 8
        self.array = []

    def __repr__(self):
        rep = "HEVCDecoderConfigurationRecord\n"
        rep += "  configuration_version: " + str(self.configuration_version) + "\n"
        rep += "  general_profile_space: " + str(self.general_profile_space) + "\n"
        rep += "  general_tier_flag: " + str(bin(self.general_tier_flag)) + "\n"
        rep += "  general_profile_idc: " + str(self.general_profile_idc) + "\n"
        rep += (
            "  general_profile_compat_flags: "
            + str(bin(self.general_profile_compat_flags))
            + "\n"
        )
        rep += (
            "  general_const_indicator_flags: "
            + str(bin(self.general_const_indicator_flags))
            + "\n"
        )
        rep += "  general_level_idc: " + str(self.general_level_idc) + "\n"
        rep += (
            "  min_spatial_segmentation_idc: "
            + str(self.min_spatial_segmentation_idc)
            + "\n"
        )
        rep += "  parallelism_type: " + str(self.parallelism_type) + "\n"
        rep += "  chroma_format: " + str(self.chroma_format) + "\n"
        rep += "  bit_depth_luma_minus_8: " + str(self.bit_depth_luma_minus_8) + "\n"
        rep += (
            "  bit_depth_chroma_minus_8: " + str(self.bit_depth_chroma_minus_8) + "\n"
        )
        rep += "  avg_frame_rate: " + str(self.avg_frame_rate) + "\n"
        rep += "  constant_frame_rate: " + str(self.constant_frame_rate) + "\n"
        rep += "  num_temporal_layers: " + str(self.num_temporal_layers) + "\n"
        rep += "  temporal_id_nested: " + str(self.temporal_id_nested) + "\n"
        rep += "  length_size_minus_1: " + str(self.length_size_minus_1)
        # rep += '  array: ' + \
        #    str(self.array) + '\n'
        return indent(rep)

    def read(self, reader: BinaryIO):
        self.configuration_version = br.buffer_read_int(reader, 1)
        #
        byte = br.buffer_read_int(reader, 1)
        self.general_profile_space = (byte >> 6) & 0b11
        self.general_tier_flag = (byte >> 5) & 0b1
        self.general_profile_idc = byte & 0b11111  # 5
        #
        self.general_profile_compat_flags = br.buffer_read_int(reader, 4)  # 32
        self.general_const_indicator_flags = br.buffer_read_int(reader, 6)  # 48
        self.general_level_idc = br.buffer_read_int(reader, 1)  # 8
        #
        byte = br.buffer_read_int(reader, 1)
        self.reserved1 = (byte >> 4) & 0b1111
        msbyte = (byte & 0b1111) << 8
        lsbyte = br.buffer_read_int(reader, 1)
        self.min_spatial_segmentation_idc = (msbyte << 8) | lsbyte
        #
        byte = br.buffer_read_int(reader, 1)
        self.reserved2 = (byte >> 2) & 0b111111
        self.parallelism_type = byte & 0b11
        #
        byte = br.buffer_read_int(reader, 1)
        self.reserved3 = (byte >> 2) & 0b111111
        self.chroma_format = byte & 0b11  # 2
        #
        byte = br.buffer_read_int(reader, 1)
        self.reserved4 = (byte >> 3) & 0b11111
        self.bit_depth_luma_minus_8 = byte & 0b111  # 3
        #
        byte = br.buffer_read_int(reader, 1)
        self.reserved5 = (byte >> 3) & 0b11111
        self.bit_depth_chroma_minus_8 = byte & 0b111  # 3
        #
        self.avg_frame_rate = br.buffer_read_int(reader, 2)  # 16
        #
        byte = br.buffer_read_int(reader, 1)
        self.constant_frame_rate = (byte >> 6) & 0b11  # 2
        self.num_temporal_layers = (byte >> 3) & 0b11  # 2
        self.temporal_id_nested = (byte >> 2) & 0b1  # 1
        self.length_size_minus_1 = byte & 0b11
        #
        num_of_arrays = br.buffer_read_int(reader, 1)  # 8
        for _ in range(num_of_arrays):
            self.array.append(self.__read_item(reader))

    def __read_item(self, reader: BinaryIO):
        item = {}
        byte = br.buffer_read_int(reader, 1)
        item["array_completeness"] = (byte >> 7) & 0b1
        item["nal_unit_type"] = byte & 0b111111

        num_nalus = br.buffer_read_int(reader, 2)
        item["nal_units"] = []
        for _ in range(num_nalus):
            nal_unit_len = br.buffer_read_int(reader, 2)
            nal_unit = reader.read(nal_unit_len)
            item["nal_units"].append(nal_unit)
        return item


### hvc end ###


### other start?? ###

# i've no idea what this tag is, but it exists in avif files
class Av1c(Box):
    box_type = "av1C"

    def __init__(self, size):
        super().__init__(size=size)

    def read(self, reader: BinaryIO):
        self.raw = reader.read(self.get_box_size())


### other end ###


CLASS_MAP = {
    "dref": DataReferenceBox,
    "url": DataEntryUrlBox,
    "urn": DataEntryUrnBox,
    "hdlr": HandlerReferenceBox,
    "iinf": ItemInformationBox,
    "infe": ItemInfomationEntry,
    "iloc": ItemLocationBox,
    "ipro": ItemProtectionBox,
    "ispe": ImageSpatialExtents,
    "ipma": ItemPropertyAssociation,
    "mdhd": MediaHeaderBox,
    "meta": MetaBox,
    "vmhd": VideoMediaHeaderBox,
    "smhd": SoundMediaHeaderBox,
    "hmhd": HintMediaHeaderBox,
    "nmhd": NullMediaHeaderBox,
    "mvhd": MovieHeaderBox,
    "pitm": PrimaryItemBox,
    "schm": SchemeTypeBox,
    "stsd": SampleDescriptionBox,
    "stco": ChunkOffsetBox,
    "stsc": SampleToChunkBox,
    "stss": SyncSampleBox,
    "stsz": SampleSizeBox,
    "stts": TimeToSampleBox,
    "tkhd": TrackHeaderBox,
    "ccst": ccst,
    "dinf": DataInformationBox,
    "ftyp": FileTypeBox,
    "iprp": ItemPropertiesBox,
    "ipco": ItemPropertyContainer,
    "pasp": PixelAspectRatio,
    "colr": ColorInformation,
    "pixi": PixelInformation,
    "rloc": RelativeInformation,
    "mdat": MediaDataBox,
    "mdia": MediaBox,
    "minf": MediaInformationBox,
    "moov": MovieBox,
    "sinf": ProtectionSchemeInfoBox,
    "frma": OriginalFormatBox,
    "schi": SchemeInformationBox,
    "stbl": SampleTableBox,
    "hint": HintSampleEntry,
    "hvc1": HEVCSampleEntry,
    "vide": VisualSampleEntry,
    "soun": AudioSampleEntry,
    "btrt": BitRateBox,
    "trak": TrackBox,
    "hvcC": HEVCConfigurationBox,
    "av1C": Av1c,
}
