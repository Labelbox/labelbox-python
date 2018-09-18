from io import BytesIO

import labelbox.lbx as lbx
import numpy as np
from PIL import Image
import pytest
import struct


@pytest.fixture
def im_png(datadir):
    with open(datadir.join('sample.png'), 'rb') as f:
        yield Image.open(BytesIO(f.read()))


@pytest.fixture
def lbx_sample(datadir):
    with open(datadir.join('sample.lbx'), 'rb') as f:
        yield f


def test_lbx_decode(lbx_sample):
    im = lbx.decode(lbx_sample)
    assert im.size == (500, 375)


def test_lbx_encode(im_png):
    colormap = [
        np.array([0, 0, 128]),
        np.array([0, 128, 0]),
    ]
    lbx_encoded = lbx.encode(im_png, colormap)
    version, width, height = map(lambda x: x[0], struct.iter_unpack('<i', lbx_encoded.read(12)))
    assert version == 1
    assert width == 500
    assert height == 375


def test_identity(im_png):
    colormap = [
        np.array([0, 0, 128]),
        np.array([0, 128, 0]),
    ]
    assert np.all(np.array(lbx.decode(lbx.encode(im_png, colormap))) == np.array(im_png))
