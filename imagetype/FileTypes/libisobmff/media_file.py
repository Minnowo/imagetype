# -*- coding: utf-8 -*-

from . import boxes


class MediaFile(object):
    def __init__(self):
        self.ftyp: boxes.FileTypeBox = None
        self.mdats: boxes.MediaDataBox = []
        self.meta: boxes.MetaBox = None
        self.moov: boxes.MovieBox = None
        self.subboxes: boxes.Box = {}

    def __repr__(self):
        rep = self.ftyp.__repr__() + "\n"
        rep += self.meta.__repr__() + "\n"
        rep += self.moov.__repr__() + "\n"
        for mdat in self.mdats:
            rep += mdat.__repr__() + "\n"
        return "ISOBaseMediaFile\n" + boxes.indent(rep)

    def read(self, file_name):

        with open(file_name, "rb") as file:

            while True:

                box = boxes.read_box(file)

                if not box:
                    break

                if box.box_type == "mdat":
                    self.mdats.append(box)
                else:
                    self.__setattr__(box.box_type, box)
                    self.subboxes[box.box_type] = box

    def show_all(self, subboxes: dict):

        for key, value in subboxes.items():

            self.show_all(value.subboxes)

            print(key)

            if value.raw != b"":
                print(value.raw)

            print()

    def _get_box(self, box, boxname):

        for key, value in box.subboxes.items():

            if key == boxname:
                return value

            _ = self._get_box(value, boxname)

            if _ is not None:
                return _

        return None

    def get_box(self, boxname):

        return self._get_box(self, boxname)
