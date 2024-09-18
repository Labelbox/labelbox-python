from functools import lru_cache
import math
import logging
from enum import Enum
from typing import Optional, List, Tuple, Any, Union, Dict, Callable
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

import requests
import numpy as np
from google.api_core import retry
from PIL import Image
from pyproj import Transformer
from pygeotile.point import Point as PygeoPoint

from labelbox.data.annotation_types import Rectangle, Point, Line, Polygon
from .base_data import BaseData
from .raster import RasterData
from pydantic import BaseModel, field_validator, model_validator, ConfigDict

VALID_LAT_RANGE = range(-90, 90)
VALID_LNG_RANGE = range(-180, 180)
DEFAULT_TMS_TILE_SIZE = 256
TILE_DOWNLOAD_CONCURRENCY = 4

logger = logging.getLogger(__name__)

VectorTool = Union[Point, Line, Rectangle, Polygon]


class EPSG(Enum):
    """Provides the EPSG for tiled image assets that are currently supported.

    SIMPLEPIXEL is Simple that can be used to obtain the pixel space coordinates

    >>> epsg = EPSG()
    """

    SIMPLEPIXEL = 1
    EPSG4326 = 4326
    EPSG3857 = 3857


class TiledBounds(BaseModel):
    """Bounds for a tiled image asset related to the relevant epsg.

    Bounds should be Point objects.

    >>> bounds = TiledBounds(epsg=EPSG.EPSG4326,
            bounds=[
                Point(x=-99.21052827588443, y=19.405662413477728),
                Point(x=-99.20534818927473, y=19.400498983095076)
            ])
    """

    epsg: EPSG
    bounds: List[Point]

    @field_validator("bounds")
    def validate_bounds_not_equal(cls, bounds):
        first_bound = bounds[0]
        second_bound = bounds[1]

        if first_bound.x == second_bound.x or first_bound.y == second_bound.y:
            raise ValueError(
                f"Bounds on either axes cannot be equal, currently {bounds}"
            )
        return bounds

    # validate bounds are within lat,lng range if they are EPSG4326
    @model_validator(mode="after")
    def validate_bounds_lat_lng(self):
        epsg = self.epsg
        bounds = self.bounds

        if epsg == EPSG.EPSG4326:
            for bound in bounds:
                lat, lng = bound.y, bound.x
                if (
                    int(lng) not in VALID_LNG_RANGE
                    or int(lat) not in VALID_LAT_RANGE
                ):
                    raise ValueError(
                        f"Invalid lat/lng bounds. Found {bounds}. "
                        f"lat must be in {VALID_LAT_RANGE}. "
                        f"lng must be in {VALID_LNG_RANGE}."
                    )
        return self


class EPSGTransformer(BaseModel):
    """Transformer class between different EPSG's. Useful when wanting to project
    in different formats.
    """

    transformer: Any
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @staticmethod
    def _is_simple(epsg: EPSG) -> bool:
        return epsg == EPSG.SIMPLEPIXEL

    @staticmethod
    def _get_ranges(bounds: np.ndarray) -> Tuple[int, int]:
        """helper function to get the range between bounds.

        returns a tuple (x_range, y_range)"""
        x_range = np.max(bounds[:, 0]) - np.min(bounds[:, 0])
        y_range = np.max(bounds[:, 1]) - np.min(bounds[:, 1])
        return (x_range, y_range)

    @staticmethod
    def _min_max_x_y(bounds: np.ndarray) -> Tuple[int, int, int, int]:
        """returns the min x, max x, min y, max y of a numpy array"""
        return (
            np.min(bounds[:, 0]),
            np.max(bounds[:, 0]),
            np.min(bounds[:, 1]),
            np.max(bounds[:, 1]),
        )

    @classmethod
    def geo_and_pixel(
        cls,
        src_epsg,
        pixel_bounds: TiledBounds,
        geo_bounds: TiledBounds,
        zoom=0,
    ) -> Callable:
        """method to change from one projection to simple projection"""

        pixel_bounds = pixel_bounds.bounds
        geo_bounds_epsg = geo_bounds.epsg
        geo_bounds = geo_bounds.bounds

        local_bounds = np.array(
            [(point.x, point.y) for point in pixel_bounds], dtype=int
        )
        # convert geo bounds to pixel bounds. assumes geo bounds are in wgs84/EPS4326 per leaflet
        global_bounds = np.array(
            [
                PygeoPoint.from_latitude_longitude(
                    latitude=point.y, longitude=point.x
                ).pixels(zoom)
                for point in geo_bounds
            ]
        )

        # get the range of pixels for both sets of bounds to use as a multiplification factor
        local_x_range, local_y_range = cls._get_ranges(bounds=local_bounds)
        global_x_range, global_y_range = cls._get_ranges(bounds=global_bounds)

        if src_epsg == EPSG.SIMPLEPIXEL:

            def transform(x: int, y: int) -> Callable[[int, int], Transformer]:
                scaled_xy = (
                    x * (global_x_range) / (local_x_range),
                    y * (global_y_range) / (local_y_range),
                )

                minx, _, miny, _ = cls._min_max_x_y(bounds=global_bounds)
                x, y = map(lambda i, j: i + j, scaled_xy, (minx, miny))

                point = PygeoPoint.from_pixel(
                    pixel_x=x, pixel_y=y, zoom=zoom
                ).latitude_longitude
                # convert to the desired epsg
                return Transformer.from_crs(
                    EPSG.EPSG4326.value, geo_bounds_epsg.value, always_xy=True
                ).transform(point[1], point[0])

            return transform

        # handles 4326 from lat,lng
        elif src_epsg == EPSG.EPSG4326:

            def transform(x: int, y: int) -> Callable[[int, int], Transformer]:
                point_in_px = PygeoPoint.from_latitude_longitude(
                    latitude=y, longitude=x
                ).pixels(zoom)

                minx, _, miny, _ = cls._min_max_x_y(global_bounds)
                x, y = map(lambda i, j: i - j, point_in_px, (minx, miny))

                return (
                    x * (local_x_range) / (global_x_range),
                    y * (local_y_range) / (global_y_range),
                )

            return transform

        # handles 3857 from meters
        elif src_epsg == EPSG.EPSG3857:

            def transform(x: int, y: int) -> Callable[[int, int], Transformer]:
                point_in_px = PygeoPoint.from_meters(
                    meter_y=y, meter_x=x
                ).pixels(zoom)

                minx, _, miny, _ = cls._min_max_x_y(global_bounds)
                x, y = map(lambda i, j: i - j, point_in_px, (minx, miny))

                return (
                    x * (local_x_range) / (global_x_range),
                    y * (local_y_range) / (global_y_range),
                )

            return transform

    @classmethod
    def create_geo_to_geo_transformer(
        cls, src_epsg: EPSG, tgt_epsg: EPSG
    ) -> Callable[[int, int], Transformer]:
        """method to change from one projection to another projection.

        supports EPSG transformations not Simple.
        """
        if cls._is_simple(epsg=src_epsg) or cls._is_simple(epsg=tgt_epsg):
            raise Exception(
                f"Cannot be used for Simple transformations. Found {src_epsg} and {tgt_epsg}"
            )

        return EPSGTransformer(
            transformer=Transformer.from_crs(
                src_epsg.value, tgt_epsg.value, always_xy=True
            ).transform
        )

    @classmethod
    def create_geo_to_pixel_transformer(
        cls,
        src_epsg,
        pixel_bounds: TiledBounds,
        geo_bounds: TiledBounds,
        zoom=0,
    ) -> Callable[[int, int], Transformer]:
        """method to change from a geo projection to Simple"""

        transform_function = cls.geo_and_pixel(
            src_epsg=src_epsg,
            pixel_bounds=pixel_bounds,
            geo_bounds=geo_bounds,
            zoom=zoom,
        )
        return EPSGTransformer(transformer=transform_function)

    @classmethod
    def create_pixel_to_geo_transformer(
        cls,
        src_epsg,
        pixel_bounds: TiledBounds,
        geo_bounds: TiledBounds,
        zoom=0,
    ) -> Callable[[int, int], Transformer]:
        """method to change from a geo projection to Simple"""
        transform_function = cls.geo_and_pixel(
            src_epsg=src_epsg,
            pixel_bounds=pixel_bounds,
            geo_bounds=geo_bounds,
            zoom=zoom,
        )
        return EPSGTransformer(transformer=transform_function)

    def _get_point_obj(self, point) -> Point:
        point = self.transformer(point.x, point.y)
        return Point(x=point[0], y=point[1])

    def __call__(
        self, shape: Union[Point, Line, Rectangle, Polygon]
    ) -> Union[VectorTool, List[VectorTool]]:
        if isinstance(shape, list):
            return [self(geom) for geom in shape]
        if isinstance(shape, Point):
            return self._get_point_obj(shape)
        if isinstance(shape, Line):
            return Line(points=[self._get_point_obj(p) for p in shape.points])
        if isinstance(shape, Polygon):
            return Polygon(
                points=[self._get_point_obj(p) for p in shape.points]
            )
        if isinstance(shape, Rectangle):
            return Rectangle(
                start=self._get_point_obj(shape.start),
                end=self._get_point_obj(shape.end),
            )
        else:
            raise ValueError(f"Unsupported type found: {type(shape)}")
