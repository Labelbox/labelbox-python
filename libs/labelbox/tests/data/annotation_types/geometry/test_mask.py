import pytest

import numpy as np
import cv2

from labelbox.data.annotation_types import Point, Rectangle, Mask, MaskData
from pydantic import ValidationError
from shapely.geometry import MultiPolygon, Polygon


def test_mask():
    with pytest.raises(ValidationError):
        mask = Mask()

    mask_data = np.zeros((32, 32, 3), dtype=np.uint8)
    mask_data = cv2.rectangle(mask_data, (0, 0), (10, 10), (255, 255, 255), -1)
    mask_data = cv2.rectangle(mask_data, (20, 20), (30, 30), (0, 255, 255), -1)
    mask_data = MaskData(arr=mask_data)

    mask1 = Mask(mask=mask_data, color=(255, 255, 255))

    # Create expected geometry - a simple rectangle from (0,0) to (10,10)
    # Using geometric equality instead of exact coordinate comparison
    # to handle different coordinate ordering between OpenCV versions
    expected_polygon1 = Polygon(
        [(0.0, 0.0), (0.0, 10.0), (10.0, 10.0), (10.0, 0.0), (0.0, 0.0)]
    )
    expected_multipolygon1 = MultiPolygon([expected_polygon1])

    # Use geometric equality - both polygons represent the same shape
    assert mask1.shapely.equals(
        expected_multipolygon1
    ), f"Geometry mismatch: expected area {expected_multipolygon1.area}, got area {mask1.shapely.area}"

    # Verify that the geometry has correct area and bounds
    assert (
        abs(mask1.shapely.area - 100.0) < 1e-6
    ), f"Expected area 100, got {mask1.shapely.area}"
    assert mask1.shapely.bounds == (
        0.0,
        0.0,
        10.0,
        10.0,
    ), f"Expected bounds (0,0,10,10), got {mask1.shapely.bounds}"

    mask2 = Mask(mask=mask_data, color=(0, 255, 255))

    # Create expected geometry for the second rectangle from (20,20) to (30,30)
    expected_polygon2 = Polygon(
        [(20.0, 20.0), (20.0, 30.0), (30.0, 30.0), (30.0, 20.0), (20.0, 20.0)]
    )
    expected_multipolygon2 = MultiPolygon([expected_polygon2])

    assert mask2.shapely.equals(
        expected_multipolygon2
    ), f"Geometry mismatch: expected area {expected_multipolygon2.area}, got area {mask2.shapely.area}"

    # Verify that the geometry has correct area and bounds
    assert (
        abs(mask2.shapely.area - 100.0) < 1e-6
    ), f"Expected area 100, got {mask2.shapely.area}"
    assert mask2.shapely.bounds == (
        20.0,
        20.0,
        30.0,
        30.0,
    ), f"Expected bounds (20,20,30,30), got {mask2.shapely.bounds}"

    gt_mask = cv2.cvtColor(
        cv2.imread("tests/data/assets/mask.png"), cv2.COLOR_BGR2RGB
    )
    assert (gt_mask == mask1.mask.arr).all()
    assert (gt_mask == mask2.mask.arr).all()

    raster1 = mask1.draw()
    raster2 = mask2.draw()

    assert (raster1 != raster2).any()

    gt1 = Rectangle(start=Point(x=0, y=0), end=Point(x=10, y=10)).draw(
        height=raster1.shape[0], width=raster1.shape[1], color=(255, 255, 255)
    )
    gt2 = Rectangle(start=Point(x=20, y=20), end=Point(x=30, y=30)).draw(
        height=raster2.shape[0], width=raster2.shape[1], color=(0, 255, 255)
    )
    assert (raster1 == gt1).all()
    assert (raster2 == gt2).all()
