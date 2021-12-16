import pytest
from labelbox.data.annotation_types.geometry.point import Point
from labelbox.data.annotation_types.data.tiled_image import (EPSG, TiledBounds,
                                                             TileLayer,
                                                             TiledImageData)
from pydantic import ValidationError


@pytest.mark.parametrize("epsg", list(EPSG))
def test_epsg(epsg):
    assert isinstance(epsg, EPSG)


@pytest.mark.parametrize("epsg", list(EPSG))
def test_tiled_bounds(epsg):
    top_left = Point(x=0, y=0)
    bottom_right = Point(x=50, y=50)

    tiled_bounds = TiledBounds(epsg=epsg, bounds=[top_left, bottom_right])
    assert isinstance(tiled_bounds, TiledBounds)
    assert isinstance(tiled_bounds.epsg, EPSG)


@pytest.mark.parametrize("epsg", list(EPSG))
def test_tiled_bounds_same(epsg):
    single_bound = Point(x=0, y=0)
    with pytest.raises(ValidationError):
        tiled_bounds = TiledBounds(epsg=epsg,
                                   bounds=[single_bound, single_bound])


def test_create_tiled_image_data():
    bounds_points = [Point(x=0, y=0), Point(x=5, y=5)]
    url = "https://labelbox.s3-us-west-2.amazonaws.com/pathology/{z}/{x}/{y}.png"
    zoom_levels = (1, 10)

    tile_layer = TileLayer(url=url, name="slippy map tile")
    tile_bounds = TiledBounds(epsg=EPSG.EPSG4326, bounds=bounds_points)
    tiled_image_data = TiledImageData(tile_layer=tile_layer,
                                      tile_bounds=tile_bounds,
                                      zoom_levels=zoom_levels,
                                      version=2)
    assert isinstance(tiled_image_data, TiledImageData)
    assert tiled_image_data.tile_bounds.bounds == bounds_points
    assert tiled_image_data.tile_layer.url == url
    assert tiled_image_data.zoom_levels == zoom_levels


#TODO: create a test from 4326->SIMPLE->3857->4326
def test_epsg_projections():
    pass
