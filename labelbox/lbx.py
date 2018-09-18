"""Module for interacting with the LBX file format.

LBX File Format - lossless compression for segmented images

HEADERS
bytes 0-3 -> LBX version
bytes 4-7 -> pixel width
bytes 8-11 -> pixel height
bytes 12-15 -> decompressed bytes
bytes 16-19 -> # colors
bytes 20-23 -> # blocks

BODY
- COLORS -
- BLOCKS -

COLOR
byte 0 -> red
byte 1 -> blue
byte 2 -> green
byte 3 -> alpha (always 255)

BLOCK
bytes 0-1 -> R | G value of pixel (superpixel layer #)
bytes 2-3 -> # consecutive occurences
"""
from io import BytesIO
import itertools
import struct

import numpy as np
from PIL import Image

_BACKGROUND_RGBA = [255, 255, 255, 255]
_HEADER_LENGTH = 6 * 4


def encode(image):
    """Converts a RGB `PIL.Image` to a `io.BytesIO` with LBX encoded data.

    Args:
        image (`PIL.Image`): The image to encode.

    Returns:
        A `io.BytesIO` containing the LBX encoded image.
    """
    im = image.convert('RGBA')
    pixel_words = np.array(im).reshape(-1, 4)

    colormap = list(filter(lambda x: not np.all(x == _BACKGROUND_RGBA),
            np.unique(pixel_words, axis=0)))


    input_byte_len = len(np.array(im).flat)
    buff = BytesIO(bytes([0] * (len(colormap) * 4 + input_byte_len)))

    offset = _HEADER_LENGTH  # make room for header
    for color in colormap:
        struct.pack_into('<BBBB', buff.getbuffer(), offset, *color)
        offset += 4

    # write header
    struct.pack_into('<iiiiii', buff.getbuffer(), 0,
            1, im.width, im.height, input_byte_len, len(colormap),
            offset - len(colormap) - _HEADER_LENGTH)

    return buff


def decode(lbx):
    """Decodes a `io.BytesIO` with LBX encoded data into a `PIL.Image`.

    Args:
        lbxA (`io.BytesIO`): A byte buffer containing the LBX encoded image data.

    Returns:
        A `PIL.Image` of the decoded data.
    """
    version, width, height, byteLength, numColors, numBlocks = \
            map(lambda x: x[0], struct.iter_unpack('<i', lbx.read(_HEADER_LENGTH)))
    colormap = np.array(
            list(_grouper(
                map(lambda x: x[0],
                    struct.iter_unpack('<B', lbx.read(4 * numColors))),
                4)) +
            [_BACKGROUND_RGBA]
            )

    image_data = np.zeros((width * height, 4), dtype='uint8')
    offset = 0
    for _ in range(numBlocks):
        layer = struct.unpack('<H', lbx.read(2))[0]
        run_length = struct.unpack('<H', lbx.read(2))[0]
        image_data[offset:offset + run_length, :] = colormap[layer]
        offset += run_length
    assert offset ==  width * height, 'number of bytes read does not equal numBytes in header'

    reshaped_image = np.reshape(image_data, (height, width, 4))
    im = Image.fromarray(reshaped_image, mode='RGBA')
    return im


def _grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return itertools.zip_longest(*args, fillvalue=fillvalue)

