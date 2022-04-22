## image-size-reader
A python package used to read the width and height of images.

### Image support

This package can currently read the sizes of the following image formats:
- jpg 
- png 
- bmp
- webp
- tiff 
- gif 

### Install

Clone the [src](./src/) folder and run `python setup.py install` to install it as a package.

Alternatively you can just paste the [image_size_reader](./src/image_size_reader/) folder into any project you want.

### Usage 

```py

import image_size_reader as isr

size = isr.get_image_size("some image path here")

print(size) 

```

You can also call the decode functions directly, just make sure you have read the byte headers from the image first.

```py

from image_size_reader import decode_png

with open("sample.png", "rb") as reader:

    header = reader.read(8) # the png has a header size of 8 bytes

    # NOTE. the jpg has a header length of 3, but the decode_jpg function expects
    #       that only 2 bytes have been read from the stream, it will validate the 3rd byte

    if header == b"\x89PNG\r\n\x1a\n":

        size = decode_png(reader) # takes the byte reader

        print(size)

    else:

        print("sample.png does not have a png header")


```
