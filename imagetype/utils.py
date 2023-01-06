# Python 2.7 workaround
try:
    import pathlib
except ImportError:
    pass


_NUM_SIGNATURE_BYTES = 8192


def get_signature_bytes(path, to_read=_NUM_SIGNATURE_BYTES):
    """
    Reads file from disk and returns the first 8192 bytes
    of data representing the magic number header signature.

    Args:
        path: path string to file.

    Returns:
        First 8192 bytes of the file content as bytearray type.
    """
    with open(path, "rb") as fp:
        return bytearray(fp.read(to_read))


def signature(array, to_read=_NUM_SIGNATURE_BYTES):
    """
    Returns the first 8192 bytes of the given bytearray
    as part of the file header signature.

    Args:
        array: bytearray to extract the header signature.

    Returns:
        First 8192 bytes of the file content as bytearray type.
    """
    length = len(array)
    index = to_read if length > to_read else length

    return array[:index]


def get_bytes(obj, to_read=_NUM_SIGNATURE_BYTES):
    """
    Infers the input type and reads the first 8192 bytes,
    returning a sliced bytearray.

    Args:
        obj: path to readable, file-like object(with read() method), bytes,
        bytearray or memoryview

    Returns:
        First 8192 bytes of the file content as bytearray type.

    Raises:
        TypeError: if obj is not a supported type.
    """
    if isinstance(obj, bytearray):
        return signature(obj, to_read)

    if isinstance(obj, str):
        return get_signature_bytes(obj, to_read)

    if isinstance(obj, bytes):
        return signature(obj, to_read)

    if isinstance(obj, memoryview):
        return bytearray(signature(obj, to_read).tolist())

    if isinstance(obj, pathlib.PurePath):
        return get_signature_bytes(obj, to_read)

    if hasattr(obj, "read"):
        if hasattr(obj, "tell") and hasattr(obj, "seek"):
            start_pos = obj.tell()
            obj.seek(0)
            magic_bytes = obj.read(to_read)
            obj.seek(start_pos)
            return get_bytes(magic_bytes)
        return get_bytes(obj.read(to_read))

    raise TypeError("Unsupported type as file input: %s" % type(obj))
