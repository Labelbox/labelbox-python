import pytest
from labelbox.data.annotation_types.geometry.polygon import Polygon
from labelbox.data.annotation_types.geometry.point import Point
from labelbox.data.annotation_types.geometry.line import Line
from labelbox.data.annotation_types.geometry.rectangle import Rectangle
from labelbox.data.annotation_types.data.tiled_image import (
    EPSG,
    TiledBounds,
    TileLayer,
    TiledImageData,
    EPSGTransformer,
)
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
        tiled_bounds = TiledBounds(
            epsg=epsg, bounds=[single_bound, single_bound]
        )


def test_create_tiled_image_data():
    bounds_points = [Point(x=0, y=0), Point(x=5, y=5)]
    url = (
        "https://labelbox.s3-us-west-2.amazonaws.com/pathology/{z}/{x}/{y}.png"
    )
    zoom_levels = (1, 10)

    tile_layer = TileLayer(url=url, name="slippy map tile")
    tile_bounds = TiledBounds(epsg=EPSG.EPSG4326, bounds=bounds_points)
    tiled_image_data = TiledImageData(
        tile_layer=tile_layer,
        tile_bounds=tile_bounds,
        zoom_levels=zoom_levels,
        version=2,
    )
    assert isinstance(tiled_image_data, TiledImageData)
    assert tiled_image_data.tile_bounds.bounds == bounds_points
    assert tiled_image_data.tile_layer.url == url
    assert tiled_image_data.zoom_levels == zoom_levels


def test_epsg_point_projections():
    zoom = 4

    bounds_simple = TiledBounds(
        epsg=EPSG.SIMPLEPIXEL, bounds=[Point(x=0, y=0), Point(x=256, y=256)]
    )

    bounds_3857 = TiledBounds(
        epsg=EPSG.EPSG3857,
        bounds=[
            Point(x=-104.150390625, y=30.789036751261136),
            Point(x=-81.8701171875, y=45.920587344733654),
        ],
    )
    bounds_4326 = TiledBounds(
        epsg=EPSG.EPSG4326,
        bounds=[
            Point(x=-104.150390625, y=30.789036751261136),
            Point(x=-81.8701171875, y=45.920587344733654),
        ],
    )

    point = Point(x=-11016716.012685884, y=5312679.21393289)
    point_two = Point(x=-12016716.012685884, y=5212679.21393289)
    point_three = Point(x=-13016716.012685884, y=5412679.21393289)

    line = Line(points=[point, point_two, point_three])
    polygon = Polygon(points=[point, point_two, point_three])
    rectangle = Rectangle(start=point, end=point_three)

    shapes_to_test = [point, line, polygon, rectangle]

    transformer_3857_simple = EPSGTransformer.create_geo_to_pixel_transformer(
        src_epsg=EPSG.EPSG3857,
        pixel_bounds=bounds_simple,
        geo_bounds=bounds_3857,
        zoom=zoom,
    )
    transformer_3857_4326 = EPSGTransformer.create_geo_to_geo_transformer(
        src_epsg=EPSG.EPSG3857,
        tgt_epsg=EPSG.EPSG4326,
    )
    transformer_4326_simple = EPSGTransformer.create_geo_to_pixel_transformer(
        src_epsg=EPSG.EPSG4326,
        pixel_bounds=bounds_simple,
        geo_bounds=bounds_4326,
        zoom=zoom,
    )

    for shape in shapes_to_test:
        shape_simple = transformer_3857_simple(shape=shape)

        shape_4326 = transformer_3857_4326(shape=shape)

        other_simple_shape = transformer_4326_simple(shape=shape_4326)

        assert shape_simple == other_simple_shape
