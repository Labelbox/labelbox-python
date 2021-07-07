from PIL import Image
import numpy as np
from io import BytesIO
from pydantic import ValidationError
import urllib.request
import pytest

from labelbox.data.annotation_types.data.raster import RasterData
from labelbox.data.annotation_types.reference import DataRowRef


def test_validate_schema():
    with pytest.raises(ValidationError):
        data = RasterData()

def test_im_bytes():
    data = (np.random.random((32, 32, 3)) * 255).astype(np.uint8)
    im_bytes = BytesIO()
    Image.fromarray(data).save(im_bytes, format="PNG")
    raster_data = RasterData(im_bytes=im_bytes.getvalue())
    data_ = raster_data.numpy
    assert np.all(data == data_)

def test_im_url():
    raster_data = RasterData(url="https://picsum.photos/id/829/200/300")
    data_ = raster_data.numpy
    assert data_.shape == (300,200,3)

def test_im_path():
    img_path = "/tmp/img.jpg"
    urllib.request.urlretrieve("https://picsum.photos/id/829/200/300", img_path)
    raster_data = RasterData(file_path=img_path)
    data_ = raster_data.numpy
    assert data_.shape == (300,200,3)

def test_ref():
    external_id = "external_id"
    uid = "uid"
    data = RasterData(im_bytes = b'', data_row_ref = DataRowRef(external_id = external_id, uid = uid))
    assert data.data_row_ref.external_id == external_id
    assert data.data_row_ref.uid == uid
