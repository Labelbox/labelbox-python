import pytest
import cv2

from labelbox.data.annotation_types.geometry import Point, Line
from pydantic import ValidationError


def test_line():
    with pytest.raises(ValidationError):
        line = Line()

    with pytest.raises(ValidationError):
        line = Line(points=[[0, 1], [2, 3]])

    points = [[0, 1], [0, 2], [2, 2]]
    expected = {"coordinates": [points], "type": "MultiLineString"}
    line = Line(points=[Point(x=x, y=y) for x, y in points])
    assert line.geometry == expected
    expected["coordinates"] = tuple([tuple([tuple(x) for x in points])])
    assert line.shapely.__geo_interface__ == expected

    raster = line.draw(height=32, width=32, thickness=1)
    assert (cv2.imread("tests/data/assets/line.png") == raster).all()
