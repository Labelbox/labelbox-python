import pytest
import cv2

from labelbox.data.annotation_types import Point
from labelbox import pydantic_compat


def test_point():
    with pytest.raises(pydantic_compat.ValidationError):
        line = Point()

    with pytest.raises(TypeError):
        line = Point([0, 1])

    point = Point(x=0, y=1)
    expected = {"coordinates": [0, 1], "type": "Point"}
    assert point.geometry == expected
    expected['coordinates'] = tuple(expected['coordinates'])
    assert point.shapely.__geo_interface__ == expected

    raster = point.draw(height=32, width=32, thickness=1)
    assert (cv2.imread("tests/data/assets/point.png") == raster).all()
