import urllib.request
from io import BytesIO

import numpy as np
import pytest
from PIL import Image

from labelbox.data.annotation_types.data import GenericDataRowData, MaskData
from pydantic import ValidationError


def test_validate_schema():
    with pytest.raises(ValidationError):
        GenericDataRowData()


def test_im_bytes():
    data = (np.random.random((32, 32, 3)) * 255).astype(np.uint8)
    im_bytes = BytesIO()
    Image.fromarray(data).save(im_bytes, format="PNG")
    raster_data = MaskData(im_bytes=im_bytes.getvalue())
    data_ = raster_data.value
    assert np.all(data == data_)


def test_im_url():
    raster_data = GenericDataRowData(url="https://picsum.photos/id/829/200/300")
    data_ = raster_data.value
    assert data_.shape == (300, 200, 3)


def test_im_path():
    img_path = "/tmp/img.jpg"
    urllib.request.urlretrieve("https://picsum.photos/id/829/200/300", img_path)
    raster_data = GenericDataRowData(file_path=img_path)
    data_ = raster_data.value
    assert data_.shape == (300, 200, 3)


def test_ref():
    external_id = "external_id"
    uid = "uid"
    metadata = []
    media_attributes = {}
    data = GenericDataRowData(
        external_id=external_id,
        uid=uid,
        metadata=metadata,
        media_attributes=media_attributes,
    )
    assert data.external_id == external_id
    assert data.uid == uid
    assert data.media_attributes == media_attributes
    assert data.metadata == metadata
