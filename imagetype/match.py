from .utils import get_bytes
from .FileTypes import IMAGE as image_matchers


def match(obj, matchers):
    """
    Matches the given input against the available
    file type matchers.

    Args:
        obj: path to file, bytes or bytearray.

    Returns:
        Type instance if type matches. Otherwise None.

    Raises:
        TypeError: if obj is not a supported type.
    """
    buf = get_bytes(obj)

    for matcher in matchers:
        if matcher.match(buf):
            return matcher

    return None


def image_match(obj):
    """
    Matches the given input against the available
    image type matchers.

    Args:
        obj: path to file, bytes or bytearray.

    Returns:
        Type instance if matches. Otherwise None.

    Raises:
        TypeError: if obj is not a supported type.
    """
    return match(obj, image_matchers)
