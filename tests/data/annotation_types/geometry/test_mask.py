from pydantic import ValidationError
import pytest

import numpy as np
import cv2

from labelbox.data.annotation_types.geometry import Point
from labelbox.data.annotation_types.geometry import Mask
from labelbox.data.annotation_types.data.raster import RasterData


def test_mask():
    with pytest.raises(ValidationError):
        mask = Mask()

    mask_data = np.zeros((32, 32, 3), dtype=np.uint8)
    mask_data = cv2.rectangle(mask_data, (0, 0), (10, 10), (255, 255, 255), 1)
    mask_data = cv2.rectangle(mask_data, (20, 20), (30, 30), (0, 255, 255), 1)
    mask_data = RasterData(arr=mask_data)

    mask1 = Mask(mask=mask_data, color_rgb=(255, 255, 255))
    expected1 = {
        'type':
            'MultiPolygon',
        'coordinates': [(((0.0, 0.0), (0.0, 11.0), (11.0, 11.0), (11.0, 0.0),
                          (0.0, 0.0)), ((1.0, 1.0), (1.0, 10.0), (10.0, 10.0),
                                        (10.0, 1.0), (1.0, 1.0)))]
    }
    assert mask1.geometry == expected1
    assert mask1.shapely.__geo_interface__ == expected1

    mask2 = Mask(mask=mask_data, color_rgb=(0, 255, 255))
    expected2 = {
        'type':
            'MultiPolygon',
        'coordinates': [(((20.0, 20.0), (20.0, 31.0), (31.0, 31.0),
                          (31.0, 20.0), (20.0, 20.0)),
                         ((21.0, 21.0), (21.0, 30.0), (30.0, 30.0),
                          (30.0, 21.0), (21.0, 21.0)))]
    }
    assert mask2.geometry == expected2
    assert mask2.shapely.__geo_interface__ == expected2

    mask1.raster()
    raster2 = mask2.raster()
    assert (cv2.cvtColor(cv2.imread("tests/data/assets/mask.png"),
                         cv2.COLOR_BGR2RGB) == raster2).all()
