# -*- coding: utf-8 -*-

# this is a modified copy of:
# https://github.com/m-hiki/isobmff
#
# i think this is out of date, at least it works with some pictures,
# but for others it doesn't get all the boxes, and again,
# i can't find much online for the isobmff format so tough to change it
# still gonna include this code in case it's useful

from .media_file import MediaFile
from .boxes import *
