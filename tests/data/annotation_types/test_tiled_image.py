import pytest
from labelbox.data.annotation_types.data import tiled_image
from labelbox.data.annotation_types.geometry.point import Point
from labelbox.data.annotation_types.data.tiled_image import (EPSG, TiledBounds,
                                                             TileLayer)
from pydantic import ValidationError


@pytest.mark.parametrize("epsg", list(EPSG))
def test_epsg(epsg):
    assert isinstance(epsg, EPSG)


@pytest.mark.parametrize("epsg", list(EPSG))
def test_tiled_bounds(epsg):
    top_left = Point(x=0, y=0)
    bottom_right = Point(x=100, y=100)

    tiled_bounds = TiledBounds(epsg=epsg, bounds=[top_left, bottom_right])
    assert isinstance(tiled_bounds, TiledBounds)
    assert isinstance(tiled_bounds.epsg, EPSG)


@pytest.mark.parametrize("epsg", list(EPSG))
def test_tiled_bounds_same(epsg):
    single_bound = Point(x=0, y=0)
    with pytest.raises(ValidationError):
        tiled_bounds = TiledBounds(epsg=epsg,
                                   bounds=[single_bound, single_bound])
