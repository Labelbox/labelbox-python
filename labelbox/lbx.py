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
import logging
import struct
from typing import List

import numpy as np
from PIL import Image

LOGGER = logging.getLogger(__name__)

# NOTE: image-segmentation front-end requires background pixels to be white to
#       render them transparent
BACKGROUND_RGBA = np.array([255, 255, 255, 255], dtype=np.uint8)
BACKGROUND_RGBA.flags.writeable = False

_HEADER_LENGTH = 6 * 4


def encode(image_in: Image, colormap: List[np.array]) -> BytesIO:
    """Converts a RGB `Image` representing a segmentation map into the LBX data format.

    Given a segmentation map representing an image, convert it to the LBX format.
    Background pixels should be represented using the `BACKGROUND_RGBA` RGBA value.

    Args:
        image_in: The image to encode.
        colormap: Ordered list of `np.array`s each of length 3 representing a
                  RGB color. Do not include `BACKGROUND_RGBA`; it will be automatically
                  accounted for. Every pixel in `image_in` must match some entry in this
                  list. The ordering of this list determines which colors map to which
                  class labels in the project ontology.

    Returns:
        The LBX encoded bytes.
    """
    image = image_in.convert('RGBA')
    pixel_words = np.array(image).reshape(-1, 4)
    pixel_words.flags.writeable = False

    colormap = list(map(lambda color: np.append(color, 255).astype(np.uint8), colormap))

    input_byte_len = len(np.array(image).flat)
    buff = BytesIO(bytes([0] * (len(colormap) * 4 + input_byte_len)))

    offset = _HEADER_LENGTH  # make room for header

    def _color_to_key(color):
        return hash(color.tostring())

    color_dict = dict()
    color_dict[_color_to_key(BACKGROUND_RGBA)] = 0  # manually add bg
    for i, color in enumerate(colormap):
        color.flags.writeable = False
        struct.pack_into('<BBBB', buff.getbuffer(), offset, *color)
        color_dict[_color_to_key(color)] = i+1
        offset += 4

    count = 0
    pixel_ints = np.apply_along_axis(_color_to_key, 1, pixel_words)
    for i, pixel_int in enumerate(pixel_ints):
        count += 1
        if i+1 == len(pixel_ints) \
                or not pixel_int == pixel_ints[i+1] \
                or count > 65534:
            try:
                struct.pack_into('<HH', buff.getbuffer(), offset, color_dict[pixel_int], count)
                offset += 4
                count = 0
            except KeyError as exc:
                LOGGER.error('Could not find color %s in colormap', pixel_words[i])
                if np.all(pixel_words[i] == np.array([0, 0, 0, 0])):
                    LOGGER.error('Did you remember to set background pixels to `BACKGROUND_RGBA`?')
                raise exc

    # write header
    struct.pack_into(
        '<iiiiii', buff.getbuffer(), 0,
        1, image.width, image.height, input_byte_len,
        len(colormap), offset - len(colormap)*4 - _HEADER_LENGTH)

    return buff


def decode(lbx: BytesIO) -> Image:
    """Decodes LBX encoded byte data into an image.

    Args:
        lbx: A byte buffer containing the LBX encoded image data.

    Returns:
        A RGBA image of the decoded data.
    """
    version, width, height, byte_length, num_colors, num_blocks =\
        struct.unpack('<' + 'i'*int(_HEADER_LENGTH/4), lbx.read(_HEADER_LENGTH))
    assert version == 1, 'only LBX v1 format is supported'

    colormap = np.array(
        [BACKGROUND_RGBA] +
        list(_grouper(struct.unpack('<' + 'B'*4*num_colors, lbx.read(4 * num_colors)), 4)))

    image_data = np.zeros((width * height, 4), dtype='uint8')
    offset = 0
    for _ in range(num_blocks):
        layer, run_length = struct.unpack('<HH', lbx.read(4))
        image_data[offset:offset + run_length, :] = colormap[layer]
        offset += run_length
    assert 4*offset == byte_length, \
        'number of bytes read does not equal num bytes specified in header'

    reshaped_image = np.reshape(image_data, (height, width, 4))
    return Image.fromarray(reshaped_image, mode='RGBA')


def _grouper(iterable, group_size, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * group_size
    return itertools.zip_longest(*args, fillvalue=fillvalue)
