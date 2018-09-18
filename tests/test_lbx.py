from PIL import Image
import labelbox.lbx as lbx

def test_identity(datadir):
    im = Image.open(datadir.join('PNG_transparency_demonstration_2.png'))
    print(im)
    assert np.array(lbx.decode(lbx.encode(im))) == np.array(im)

