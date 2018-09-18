from io import BytesIO

import labelbox.lbx as lbx
import numpy as np
from PIL import Image

def test_identity(datadir):
    with open(datadir.join('PNG_transparency_demonstration_2.png'), 'rb') as f:
        im = Image.open(BytesIO(f.read()))
    assert np.all(np.array(lbx.decode(lbx.encode(im))) == np.array(im))

