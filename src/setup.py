# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.

import re
import os.path
from setuptools import setup, find_packages

def read(fname):
    path = os.path.join(os.path.dirname(__file__), fname)
    with open(path, encoding="utf-8") as file:
        return file.read()

REQUIREMENTS = []

# get version without importing the package
VERSION = re.search(r'__version__\s*=\s*"([^"]+)"', read("image_size_reader\\__init__.py")).group(1)

DESCRIPTION = ("Library for reading image sizes")

setup(
    name                 = "image_size_reader",
    version              = VERSION,
    description          = DESCRIPTION,
    url                  = "https://github.com/Minnowo/image-size-reader",
    download_url         = "https://github.com/Minnowo/image-size-reader",
    author               = "Alice Nyaa",
    author_email         = "",
    maintainer           = "Minnowo",
    maintainer_email     = "",
    include_package_data = True,
    license              = "GPLv3",

    # i have no idea what version of python this needs i'm using 3.7.6
    # this package only uses the python std with no imports so probably 3.x.x+ 
    python_requires = ">=3.4", 

    install_requires=REQUIREMENTS,
    
    zip_safe=False,

    packages=find_packages(),

    entry_points={
        "console_scripts": [
            "image-size-reader = image_size_reader:init",
        ],
    },
    
    keywords="image size dimensions width height",

    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Utilities",
    ],
    test_suite="test"
)