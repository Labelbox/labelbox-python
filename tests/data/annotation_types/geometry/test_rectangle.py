import cv2
import pytest

from labelbox.data.annotation_types import Point, Rectangle
from labelbox import pydantic_compat


def test_rectangle():
    with pytest.raises(pydantic_compat.ValidationError):
        rectangle = Rectangle()

    rectangle = Rectangle(start=Point(x=0, y=1), end=Point(x=10, y=10))
    points = [[[0.0, 1.0], [0.0, 10.0], [10.0, 10.0], [10.0, 1.0], [0.0, 1.0]]]
    expected = {"coordinates": points, "type": "Polygon"}
    assert rectangle.geometry == expected
    expected['coordinates'] = tuple([tuple([tuple(x) for x in points[0]])])
    assert rectangle.shapely.__geo_interface__ == expected

    raster = rectangle.draw(height=32, width=32)
    assert (cv2.imread("tests/data/assets/rectangle.png") == raster).all()

    xyhw = Rectangle.from_xyhw(0., 0, 10, 10)
    assert xyhw.start == Point(x=0, y=0.)
    assert xyhw.end == Point(x=10, y=10.0)
