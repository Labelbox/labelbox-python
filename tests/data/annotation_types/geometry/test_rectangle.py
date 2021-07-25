from pydantic import ValidationError
import pytest
import cv2

from labelbox.data.annotation_types import Point, Rectangle


def test_rectangle():
    with pytest.raises(ValidationError):
        rectangle = Rectangle()

    rectangle = Rectangle(start=Point(x=0, y=1), end=Point(x=10, y=10))
    points = [[[0.0, 1.0], [0.0, 10.0], [10.0, 10.0], [10.0, 1.0], [0.0, 1.0]]]
    expected = {"coordinates": points, "type": "Polygon"}
    assert rectangle.geometry == expected
    expected['coordinates'] = tuple([tuple([tuple(x) for x in points[0]])])
    assert rectangle.shapely.__geo_interface__ == expected

    raster = rectangle.raster(height=32, width=32)
    assert (cv2.imread("tests/data/assets/rectangle.png") == raster).all()
