

__version__ = "0.0.1"




def decode_tiff(io_byte_reader, endian : str):
    """ 
    Reads the Width and Height of a .tiff image encoded with the given endian format (big/little).

    This assumes the given file stream has already read the header bytes (length of 4).

    Returns (int, int)
    """

    idf_start = int.from_bytes(io_byte_reader.read(4), byteorder=endian)

    io_byte_reader.seek(idf_start)

    number_of_idf = int.from_bytes(io_byte_reader.read(2), byteorder=endian)

    width  = 0 
    height = 0 

    # https://www.awaresystems.be/imaging/tiff/tifftags/baseline.html
    for _ in range(number_of_idf):

        field = int.from_bytes(io_byte_reader.read(2), byteorder=endian)

        if field == 256:

            io_byte_reader.read(6)

            width = int.from_bytes(io_byte_reader.read(4), byteorder=endian)

        elif field == 257:

            io_byte_reader.read(6)

            height = int.from_bytes(io_byte_reader.read(4), byteorder=endian)

        else:

            io_byte_reader.read(10)

        if width > 0 and height > 0:
            
            return (width, height)

    return (width, height)

def decode_tiff_be(io_byte_reader):
    """ 
    Reads the Width and Height of a .tiff image encoded with the big endian format.

    This assumes the given file stream has already read the header bytes (length of 4).

    Returns (int, int)
    """

    return decode_tiff(io_byte_reader, "big")

def decode_tiff_le(io_byte_reader):
    """ 
    Reads the Width and Height of a .tiff image encoded with the little endian format.

    This assumes the given file stream has already read the header bytes (length of 4).

    Returns (int, int)
    """

    return decode_tiff(io_byte_reader, "little")

def decode_webp(io_byte_reader):
    """ 
    Reads the Width and Height of a .webp image.

    This assumes the given file stream has already read the header bytes (length of 4).

    Returns (int, int)
    """

    # see https://developers.google.com/speed/webp/docs/riff_container 
    #     https://datatracker.ietf.org/doc/html/rfc6386

    io_byte_reader.read(4)

    if io_byte_reader.read(4) != b"WEBP":
        return (0, 0)

    webp_type = io_byte_reader.read(4)

    # lossy webp 
    if webp_type == b"VP8 ":
        
        io_byte_reader.read(7)

        if io_byte_reader.read(3) != b'\x9d\x01*':
            return (0, 0)
        
        return (
            int.from_bytes(io_byte_reader.read(2), byteorder='little'),
            int.from_bytes(io_byte_reader.read(2), byteorder='little')
        )


    # lossless webp
    if webp_type == b"VP8L":

        io_byte_reader.read(4)

        if io_byte_reader.read(1) != b"\x2f": # 1 byte signature
            return (0, 0)

        b = io_byte_reader.read(4)

        # https://wiki.tcl-lang.org/page/Reading+WEBP+image+dimensions
        # i just converted the hex to decimal cause it's cleaner 
        # 63  = 0x3F
        # 15  = 0x0F
        # 192 = 0xC0
        return (
            1 + (((b[1] & 63) << 8)  | b[0]),
            1 + (((b[3] & 15) << 10) | (b[2] << 2) | ((b[1] & 192) >> 6))
        )

    # extended webp
    if webp_type == b"VP8X":

        io_byte_reader.read(8)

        return (
            1 + int.from_bytes(io_byte_reader.read(3), byteorder='little'),
            1 + int.from_bytes(io_byte_reader.read(3), byteorder='little')
        )

    return (0, 0)

def decode_jpeg(io_byte_reader):
    """ 
    Reads the Width and Height of a .jpg .jpeg .jfif .jpe .jif .jfi image.

    This assumes the given file stream has already read the header bytes (length of 2).

    Returns (int, int)
    """
    # check that missing byte from the jpg header 
    while(io_byte_reader.read(1) == b"\xFF"):

        marker       = io_byte_reader.read(1)
        chunk_length = int.from_bytes(io_byte_reader.read(2), byteorder="big", signed=True)

        if marker == b"\xc0" or marker == b"\xc2":

            io_byte_reader.read(1)

            # make sure to read height before width, otherwise it's backwards 
            height = int.from_bytes(io_byte_reader.read(2), byteorder='big')
            width  = int.from_bytes(io_byte_reader.read(2), byteorder='big')

            return (width, height)

        if chunk_length < 0:
            
            # since chunk_length is a signed int16
            # we convert to a unsigned int16
            unsigned_chunk_length = chunk_length + 65536 # 1 << 16

            io_byte_reader.read(unsigned_chunk_length - 2)

        else:
            io_byte_reader.read(chunk_length - 2)

    return (0, 0)

def decode_png(io_byte_reader):
    """ 
    Reads the Width and Height of a .png image.

    This assumes the given file stream has already read the header bytes (length of 8).

    Returns (int, int)
    """

    io_byte_reader.read(8)

    return (
        int.from_bytes(io_byte_reader.read(4), byteorder='big'),
        int.from_bytes(io_byte_reader.read(4), byteorder='big')
    )

def decode_gif(io_byte_reader):
    """ 
    Reads the Width and Height of a .gif image.

    This assumes the given file stream has already read the header bytes (length of 6).

    Returns (int, int)
    """

    return (
        int.from_bytes(io_byte_reader.read(2), byteorder='little'),
        int.from_bytes(io_byte_reader.read(2), byteorder='little')
    )

def decode_bmp(io_byte_reader):
    """ 
    Reads the Width and Height of a .bmp image.

    This assumes the given file stream has already read the header bytes (length of 2).

    Returns (int, int)
    """

    io_byte_reader.read(16)

    return (
        int.from_bytes(io_byte_reader.read(4), byteorder='little'),
        int.from_bytes(io_byte_reader.read(4), byteorder='little')
    )

image_decoder_map = {
     b"BM"                : decode_bmp ,

     b"GIF89a"            : decode_gif ,
     b"GIF87a"            : decode_gif ,
    
     b"\x89PNG\r\n\x1a\n" : decode_png ,
    
    # this is uaually b"\xFF\xD8\xFF" 
    # but if we only use 2 here, we can read 2 bytes at a time when scanning
    # and just let the decode jpg function handle the 3rd byte 
     b"\xFF\xD8"          : decode_jpeg , 
    
     b"RIFF"              : decode_webp ,
    
     b"MM\x00*"           : decode_tiff_be ,
     b"II*\x00"           : decode_tiff_le ,
}


def get_image_size(path : str):
    """ 
    Gets the width and height of an image from the given file path.

    Returns 

           tuple(width : int, height : int) or
    
           (0, 0) if the file could not be read
    """
    
    # at most the header will have 8 bytes 
    # since we are reading 2 bytes at a time, we only need half this 
    MAX_FILE_HEADER_LENGTH = 4 
    MIN_FILE_HEADER_LENGTH = 2 # at least the header will have 2 bytes

    with open(path, "rb") as byte_reader:

        file_header = byte_reader.read(MIN_FILE_HEADER_LENGTH)

        for _ in range(MAX_FILE_HEADER_LENGTH):

            decode_func = image_decoder_map.get(file_header, None)

            if decode_func is not None:
                return decode_func(byte_reader)

            # since all the byte headers are an even number of bytes
            # we can read 2 at a time here 
            file_header += byte_reader.read(2)


    return (0, 0)




if __name__ == "__main__":

    import os 

    p = "..\\..\\images\\"

    for folder in ("tiff", "jpg", "webp", "gif"):
        
        folder = os.path.join(p, folder)

        for file in os.listdir(folder):

            print("=" * 32)
            print(file)
            print("detected size: ", get_image_size(os.path.join(folder, file)))
