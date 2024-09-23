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


class TileLayer(BaseModel):
    """Url that contains the tile layer. Must be in the format:

    https://c.tile.openstreetmap.org/{z}/{x}/{y}.png

    >>> layer = TileLayer(
        url="https://c.tile.openstreetmap.org/{z}/{x}/{y}.png",
        name="slippy map tile"
        )
    """

    url: str
    name: Optional[str] = "default"

    def asdict(self) -> Dict[str, str]:
        return {"tileLayerUrl": self.url, "name": self.name}

    @field_validator("url")
    def validate_url(cls, url):
        xyz_format = "/{z}/{x}/{y}"
        if xyz_format not in url:
            raise ValueError(f"{url} needs to contain {xyz_format}")
        return url


class TiledImageData(BaseData):
    """Represents tiled imagery

    If specified version is 2, converts bounds from [lng,lat] to [lat,lng]

    Requires the following args:
        tile_layer: TileLayer
        tile_bounds: TiledBounds
        zoom_levels: List[int]
    Optional args:
        max_native_zoom: int = None
        tile_size: Optional[int]
        version: int = 2
        alternative_layers: List[TileLayer]

    >>> tiled_image_data = TiledImageData(tile_layer=TileLayer,
                                  tile_bounds=TiledBounds,
                                  zoom_levels=[1, 12])
    """

    tile_layer: TileLayer
    tile_bounds: TiledBounds
    alternative_layers: List[TileLayer] = []
    zoom_levels: Tuple[int, int]
    max_native_zoom: Optional[int] = None
    tile_size: Optional[int] = DEFAULT_TMS_TILE_SIZE
    version: Optional[int] = 2
    multithread: bool = True

    def __post_init__(self) -> None:
        if self.max_native_zoom is None:
            self.max_native_zoom = self.zoom_levels[0]

    def asdict(self) -> Dict[str, str]:
        return {
            "tileLayerUrl": self.tile_layer.url,
            "bounds": [
                [self.tile_bounds.bounds[0].x, self.tile_bounds.bounds[0].y],
                [self.tile_bounds.bounds[1].x, self.tile_bounds.bounds[1].y],
            ],
            "minZoom": self.zoom_levels[0],
            "maxZoom": self.zoom_levels[1],
            "maxNativeZoom": self.max_native_zoom,
            "epsg": self.tile_bounds.epsg.name,
            "tileSize": self.tile_size,
            "alternativeLayers": [
                layer.asdict() for layer in self.alternative_layers
            ],
            "version": self.version,
        }

    def raster_data(
        self, zoom: int = 0, max_tiles: int = 32, multithread=True
    ) -> RasterData:
        """Converts the tiled image asset into a RasterData object containing an
        np.ndarray.

        Uses the minimum zoom provided to render the image.
        """
        if self.tile_bounds.epsg == EPSG.SIMPLEPIXEL:
            xstart, ystart, xend, yend = self._get_simple_image_params(zoom)
        elif self.tile_bounds.epsg == EPSG.EPSG4326:
            xstart, ystart, xend, yend = self._get_3857_image_params(
                zoom, self.tile_bounds
            )
        elif self.tile_bounds.epsg == EPSG.EPSG3857:
            # transform to 4326
            transformer = EPSGTransformer.create_geo_to_geo_transformer(
                EPSG.EPSG3857, EPSG.EPSG4326
            )
            transforming_bounds = [
                transformer(self.tile_bounds.bounds[0]),
                transformer(self.tile_bounds.bounds[1]),
            ]
            xstart, ystart, xend, yend = self._get_3857_image_params(
                zoom, transforming_bounds
            )
        else:
            raise ValueError(f"Unsupported epsg found: {self.tile_bounds.epsg}")

        self._validate_num_tiles(xstart, ystart, xend, yend, max_tiles)

        rounded_tiles, pixel_offsets = list(
            zip(
                *[
                    self._tile_to_pixel(pt)
                    for pt in [xstart, ystart, xend, yend]
                ]
            )
        )

        image = self._fetch_image_for_bounds(*rounded_tiles, zoom, multithread)
        arr = self._crop_to_bounds(image, *pixel_offsets)
        return RasterData(arr=arr)

    @property
    def value(self) -> np.ndarray:
        """Returns the value of a generated RasterData object."""
        return self.raster_data(
            self.zoom_levels[0], multithread=self.multithread
        ).value

    def _get_simple_image_params(
        self, zoom
    ) -> Tuple[float, float, float, float]:
        """Computes the x and y tile bounds for fetching an image that
        captures the entire labeling region (TiledData.bounds) given a specific zoom

        Simple has different order of x / y than lat / lng because of how leaflet behaves
        leaflet reports all points as pixel locations at a zoom of 0
        """
        xend, xstart, yend, ystart = (
            self.tile_bounds.bounds[1].x,
            self.tile_bounds.bounds[0].x,
            self.tile_bounds.bounds[1].y,
            self.tile_bounds.bounds[0].y,
        )
        return (
            *[
                x * (2 ** (zoom)) / self.tile_size
                for x in [xstart, ystart, xend, yend]
            ],
        )

    def _get_3857_image_params(
        self, zoom: int, bounds: TiledBounds
    ) -> Tuple[float, float, float, float]:
        """Computes the x and y tile bounds for fetching an image that
        captures the entire labeling region (TiledData.bounds) given a specific zoom
        """
        lat_start, lat_end = bounds.bounds[1].y, bounds.bounds[0].y
        lng_start, lng_end = bounds.bounds[1].x, bounds.bounds[0].x

        # Convert to zoom 0 tile coordinates
        xstart, ystart = self._latlng_to_tile(lat_start, lng_start)
        xend, yend = self._latlng_to_tile(lat_end, lng_end)

        # Make sure that the tiles are increasing in order
        xstart, xend = min(xstart, xend), max(xstart, xend)
        ystart, yend = min(ystart, yend), max(ystart, yend)
        return (*[pt * 2.0**zoom for pt in [xstart, ystart, xend, yend]],)

    def _latlng_to_tile(
        self, lat: float, lng: float, zoom=0
    ) -> Tuple[float, float]:
        """Converts lat/lng to 3857 tile coordinates
        Formula found here:
        https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#lon.2Flat_to_tile_numbers_2
        """
        scale = 2**zoom
        lat_rad = math.radians(lat)
        x = (lng + 180.0) / 360.0 * scale
        y = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * scale
        return x, y

    def _tile_to_pixel(self, tile: float) -> Tuple[int, int]:
        """Rounds a tile coordinate and reports the remainder in pixels"""
        rounded_tile = int(tile)
        remainder = tile - rounded_tile
        pixel_offset = int(self.tile_size * remainder)
        return rounded_tile, pixel_offset

    def _fetch_image_for_bounds(
        self,
        x_tile_start: int,
        y_tile_start: int,
        x_tile_end: int,
        y_tile_end: int,
        zoom: int,
        multithread=True,
    ) -> np.ndarray:
        """Fetches the tiles and combines them into a single image.

        If a tile cannot be fetched, a padding of expected tile size is instead added.
        """

        if multithread:
            tiles = {}
            with ThreadPoolExecutor(
                max_workers=TILE_DOWNLOAD_CONCURRENCY
            ) as exc:
                for x in range(x_tile_start, x_tile_end + 1):
                    for y in range(y_tile_start, y_tile_end + 1):
                        tiles[(x, y)] = exc.submit(self._fetch_tile, x, y, zoom)

        rows = []
        for y in range(y_tile_start, y_tile_end + 1):
            row = []
            for x in range(x_tile_start, x_tile_end + 1):
                try:
                    if multithread:
                        row.append(tiles[(x, y)].result())
                    else:
                        row.append(self._fetch_tile(x, y, zoom))
                except:
                    row.append(
                        np.zeros(
                            shape=(self.tile_size, self.tile_size, 3),
                            dtype=np.uint8,
                        )
                    )
            rows.append(np.hstack(row))

        return np.vstack(rows)

    @retry.Retry(initial=1, maximum=16, multiplier=2)
    def _fetch_tile(self, x: int, y: int, z: int) -> np.ndarray:
        """
        Fetches the image and returns an np array.
        """
        data = requests.get(self.tile_layer.url.format(x=x, y=y, z=z))
        data.raise_for_status()
        decoded = np.array(Image.open(BytesIO(data.content)))[..., :3]
        if decoded.shape[:2] != (self.tile_size, self.tile_size):
            logger.warning(f"Unexpected tile size {decoded.shape}.")
        return decoded

    def _crop_to_bounds(
        self,
        image: np.ndarray,
        x_px_start: int,
        y_px_start: int,
        x_px_end: int,
        y_px_end: int,
    ) -> np.ndarray:
        """This function slices off the excess pixels that are outside of the bounds.
        This occurs because only full tiles can be downloaded at a time.
        """

        def invert_point(pt):
            # Must have at least 1 pixel for stability.
            pt = max(pt, 1)
            # All pixel points are relative to a single tile
            # So subtracting the tile size inverts the axis
            pt = pt - self.tile_size
            return pt if pt != 0 else None

        x_px_end, y_px_end = invert_point(x_px_end), invert_point(y_px_end)
        return image[y_px_start:y_px_end, x_px_start:x_px_end, :]

    def _validate_num_tiles(
        self,
        xstart: float,
        ystart: float,
        xend: float,
        yend: float,
        max_tiles: int,
    ):
        """Calculates the number of expected tiles we would fetch.

        If this is greater than the number of max tiles, raise an error.
        """
        total_n_tiles = (yend - ystart + 1) * (xend - xstart + 1)
        if total_n_tiles > max_tiles:
            raise ValueError(
                f"Requested zoom results in {total_n_tiles} tiles."
                f"Max allowed tiles are {max_tiles}"
                f"Increase max tiles or reduce zoom level."
            )

    @field_validator("zoom_levels")
    def validate_zoom_levels(cls, zoom_levels):
        if zoom_levels[0] > zoom_levels[1]:
            raise ValueError(
                f"Order of zoom levels should be min, max. Received {zoom_levels}"
            )
        return zoom_levels


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
