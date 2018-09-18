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
from typing import List

import numpy as np
from PIL import Image

_BACKGROUND_RGBA = np.array([255, 255, 255, 255])
_BACKGROUND_RGBA.flags.writeable = False
_HEADER_LENGTH = 6 * 4


def encode(image_in: Image, colormap: List[np.array]):
    """Converts a RGB `Image` to a `io.BytesIO` with LBX encoded data.

    Args:
        image_in: The image to encode.
        colormap: Ordered list of `np.array`s each of length 3 representing
                  a RGB color. The ordering of this list determines which colors
                  map to which class labels in the project ontology.

    Returns:
        A `io.BytesIO` containing the LBX encoded image.
    """
    image = image_in.convert('RGBA')
    pixel_words = np.array(image).reshape(-1, 4)
    pixel_words.flags.writeable = False

    colormap = [np.zeros(4, dtype=np.uint8)] + \
        list(map(lambda color: np.append(color, 255).astype(np.uint8), colormap))

    input_byte_len = len(np.array(image).flat)
    buff = BytesIO(bytes([0] * (len(colormap) * 4 + input_byte_len)))

    offset = _HEADER_LENGTH  # make room for header

    def _color_to_key(color):
        return hash(color.tostring())

    color_dict = dict()
    for i, color in enumerate(colormap):
        color.flags.writeable = False
        struct.pack_into('<BBBB', buff.getbuffer(), offset, *color)
        color_dict[_color_to_key(color)] = i
        offset += 4
    color_dict[_color_to_key(_BACKGROUND_RGBA)] = len(colormap)

    count = 0
    pixel_ints = np.apply_along_axis(_color_to_key, 1, pixel_words)
    for i, pixel_int in enumerate(pixel_ints):
        count += 1
        if i+1 == len(pixel_ints) \
                or not pixel_int == pixel_ints[i+1] \
                or count > 65534:
            struct.pack_into('<HH', buff.getbuffer(), offset, color_dict[pixel_int], count)
            offset += 4
            count = 0

    # write header
    struct.pack_into(
        '<iiiiii', buff.getbuffer(), 0,
        1, image.width, image.height, input_byte_len,
        len(colormap), offset - len(colormap)*4 - _HEADER_LENGTH)

    return buff


def decode(lbx: BytesIO):
    """Decodes a `BytesIO` with LBX encoded data into a `PIL.Image`.

    Args:
        lbx: A byte buffer containing the LBX encoded image data.

    Returns:
        A `PIL.Image` of the decoded data.
    """
    version, width, height, byte_length, num_colors, num_blocks = \
        map(lambda x: x[0], struct.iter_unpack('<i', lbx.read(_HEADER_LENGTH)))
    assert version == 1, 'this method only supports LBX v1 format'

    colormap = np.array(
        list(_grouper(
            map(lambda x: x[0],
                struct.iter_unpack('<B', lbx.read(4 * num_colors))),
            4)) +
        [_BACKGROUND_RGBA])

    image_data = np.zeros((width * height, 4), dtype='uint8')
    offset = 0
    for _ in range(num_blocks):
        layer = struct.unpack('<H', lbx.read(2))[0]
        run_length = struct.unpack('<H', lbx.read(2))[0]
        image_data[offset:offset + run_length, :] = colormap[layer]
        offset += run_length
    assert 4*offset == byte_length, \
        'number of bytes read does not equal numBytes in header'

    reshaped_image = np.reshape(image_data, (height, width, 4))
    return Image.fromarray(reshaped_image, mode='RGBA')


def _grouper(iterable, group_size, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * group_size
    return itertools.zip_longest(*args, fillvalue=fillvalue)
