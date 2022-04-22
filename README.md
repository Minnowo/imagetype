## image-size-reader
A python package used to read the width and height of images.

### Install

Clone the [src](./src/) folder and run `python setup.py install` to install it as a package.

Alternatively you can just paste the [image_size_reader](./src/image_size_reader/) folder into any project you want.

### Usage 

```py

import image_size_reader as isr

size = isr.get_image_size("some image path here")

print(size) 

```