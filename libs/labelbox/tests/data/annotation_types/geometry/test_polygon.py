import pytest
import cv2

from labelbox.data.annotation_types import Polygon, Point
from labelbox import pydantic_compat


def test_polygon():
    with pytest.raises(pydantic_compat.ValidationError):
        polygon = Polygon()

    with pytest.raises(pydantic_compat.ValidationError):
        polygon = Polygon(points=[[0, 1], [2, 3]])

    with pytest.raises(pydantic_compat.ValidationError):
        polygon = Polygon(points=[Point(x=0, y=1), Point(x=0, y=1)])

    points = [[0., 1.], [0., 2.], [2., 2.], [2., 0.]]
    expected = {"coordinates": [points + [points[0]]], "type": "Polygon"}
    polygon = Polygon(points=[Point(x=x, y=y) for x, y in points])
    assert polygon.geometry == expected
    expected['coordinates'] = tuple(
        [tuple([tuple(x) for x in points + [points[0]]])])
    assert polygon.shapely.__geo_interface__ == expected

    raster = polygon.draw(10, 10)
    assert (cv2.imread("tests/data/assets/polygon.png") == raster).all()
