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
import itertools
import struct

import numpy as np
from PIL import Image


def encode(image):
    """Converts a `PIL.Image` to a `io.BytesIO` with LBX encoded data.

    Args:
        image (`PIL.Image`): The image to encode.

    Returns:
        A `io.BytesIO` containing the LBX encoded image.
    """
    return image


def decode(lbx):
    """Decodes a `io.BytesIO` with LBX encoded data into a `PIL.Image`.

    Args:
        lbxA (`io.BytesIO`): A byte buffer containing the LBX encoded image data.

    Returns:
        A `PIL.Image` of the decoded data.
    """
    version, width, height, byteLength, numColors, numBlocks = \
            map(lambda x: x[0], struct.iter_unpack('<i', lbx.read(24)))
    colormap = np.array(
            list(_grouper(
                map(lambda x: x[0],
                    struct.iter_unpack('<B', lbx.read(4 * numColors))),
                4)) +
            [[0, 0, 0, 255]]
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

