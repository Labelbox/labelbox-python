from pydantic import ValidationError
import pytest

import numpy as np
import cv2

from labelbox.data.annotation_types import Point, Rectangle, Mask, MaskData


def test_mask():
    with pytest.raises(ValidationError):
        mask = Mask()

    mask_data = np.zeros((32, 32, 3), dtype=np.uint8)
    mask_data = cv2.rectangle(mask_data, (0, 0), (10, 10), (255, 255, 255), -1)
    mask_data = cv2.rectangle(mask_data, (20, 20), (30, 30), (0, 255, 255), -1)
    mask_data = MaskData(arr=mask_data)

    mask1 = Mask(mask=mask_data, color=(255, 255, 255))

    expected1 = {
        'type':
            'MultiPolygon',
        'coordinates': [(((0.0, 0.0), (0.0, 11.0), (11.0, 11.0), (11.0, 0.0),
                          (0.0, 0.0)),)]
    }
    assert mask1.geometry == expected1
    assert mask1.shapely.__geo_interface__ == expected1

    mask2 = Mask(mask=mask_data, color=(0, 255, 255))
    expected2 = {
        'type':
            'MultiPolygon',
        'coordinates': [(((20.0, 20.0), (20.0, 31.0), (31.0, 31.0),
                          (31.0, 20.0), (20.0, 20.0)),)]
    }
    assert mask2.geometry == expected2
    assert mask2.shapely.__geo_interface__ == expected2
    gt_mask = cv2.cvtColor(cv2.imread("tests/data/assets/mask.png"),
                           cv2.COLOR_BGR2RGB)
    assert (gt_mask == mask1.mask.arr).all()
    assert (gt_mask == mask2.mask.arr).all()

    raster1 = mask1.draw()
    raster2 = mask2.draw()

    assert (raster1 != raster2).any()

    gt1 = Rectangle(start=Point(x=0, y=0),
                    end=Point(x=10, y=10)).draw(height=raster1.shape[0],
                                                width=raster1.shape[1],
                                                color=(255, 255, 255))
    gt2 = Rectangle(start=Point(x=20, y=20),
                    end=Point(x=30, y=30)).draw(height=raster2.shape[0],
                                                width=raster2.shape[1],
                                                color=(0, 255, 255))
    assert (raster1 == gt1).all()
    assert (raster2 == gt2).all()
