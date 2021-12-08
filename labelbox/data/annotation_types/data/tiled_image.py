import math
import logging
from enum import Enum
from typing import Optional, List, Tuple
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

import requests
import numpy as np

from retry import retry  #TODO not part of the package atm. need to add in?
import tensorflow as f
from PIL import Image
from pyproj import Transformer
from pydantic import BaseModel, validator, conlist
from pydantic.class_validators import root_validator

from ..geometry import Point
from .base_data import BaseData
from .raster import RasterData

VALID_LAT_RANGE = range(-90, 90)
VALID_LNG_RANGE = range(-180, 180)
DEFAULT_TMS_TILE_SIZE = 256
TILE_DOWNLOAD_CONCURRENCY = 4

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EPSG(Enum):
    """ Provides the EPSG for tiled image assets that are currently supported.
    
    SIMPLEPIXEL is Simple that can be used to obtain the pixel space coordinates

    >>> epsg = EPSG()
    """
    SIMPLEPIXEL = 1
    EPSG4326 = 4326
    EPSG3857 = 3857


class TiledBounds(BaseModel):
    """ Bounds for a tiled image asset related to the relevant epsg. 

    Bounds should be Point objects. Currently, we support bounds in EPSG 4326.

    If version of asset is 2, these should be [[lat,lng],[lat,lng]]
    If version of asset is 1, these should be [[lng,lat]],[lng,lat]]

    >>> bounds = TiledBounds(
        epsg=EPSG.4326,
        bounds=[Point(x=0, y=0),Point(x=100, y=100)]
        )
    """
    epsg: EPSG
    bounds: List[Point]

    @validator('bounds')
    def validate_bounds_not_equal(cls, bounds):
        first_bound = bounds[0]
        second_bound = bounds[1]

        if first_bound == second_bound:
            raise AssertionError(f"Bounds cannot be equal, contains {bounds}")
        return bounds

    #bounds are assumed to be in EPSG 4326 as that is what leaflet assumes
    @root_validator
    def validate_bounds_lat_lng(cls, values):
        epsg = values.get('epsg')
        bounds = values.get('bounds')

        if epsg != EPSG.SIMPLEPIXEL:
            for bound in bounds:
                lat, lng = bound.y, bound.x
                if int(lng) not in VALID_LNG_RANGE or int(
                        lat) not in VALID_LAT_RANGE:
                    raise ValueError(f"Invalid lat/lng bounds. Found {bounds}. "
                                     f"lat must be in {VALID_LAT_RANGE}. "
                                     f"lng must be in {VALID_LNG_RANGE}.")
        return values


class TileLayer(BaseModel):
    """ Url that contains the tile layer. Must be in the format:

    https://c.tile.openstreetmap.org/{z}/{x}/{y}.png

    >>> layer = TileLayer(
        url="https://c.tile.openstreetmap.org/{z}/{x}/{y}.png",
        name="slippy map tile"
        )
    """
    url: str
    name: Optional[str] = "default"

    @validator('url')
    def validate_url(cls, url):
        xyz_format = "/{z}/{x}/{y}"
        if xyz_format not in url:
            raise ValueError(f"{url} needs to contain {xyz_format}")
        return url


class TiledImageData(BaseData):
    """ Represents tiled imagery 

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
    alternative_layers: List[TileLayer] = None
    zoom_levels: Tuple[int, int]
    max_native_zoom: Optional[int] = None
    tile_size: Optional[int] = DEFAULT_TMS_TILE_SIZE
    version: Optional[int] = 2
    multithread: bool = True

    def as_raster_data(self,
                       zoom: int = 0,
                       max_tiles: int = 32,
                       multithread=True) -> RasterData:
        """Converts the tiled image asset into a RasterData object containing an
        np.ndarray.

        Uses the minimum zoom provided to render the image.
        """
        if self.tile_bounds.epsg == EPSG.SIMPLEPIXEL:
            xstart, ystart, xend, yend = self._get_simple_image_params(zoom)

        # Currently our editor doesn't support anything other than 3857.
        # Since the user provided projection is ignored by the editor
        #    we will ignore it here and assume that the projection is 3857.
        elif self.tile_bounds.epsg == EPSG.EPSG3857:
            xstart, ystart, xend, yend = self._get_3857_image_params(zoom)
        else:
            raise ValueError(
                f"Unsupported epsg found...{self.tile_bounds.epsg}")

        self._validate_num_tiles(xstart, ystart, xend, yend, max_tiles)

        rounded_tiles, pixel_offsets = list(
            zip(*[
                self._tile_to_pixel(pt) for pt in [xstart, ystart, xend, yend]
            ]))

        image = self._fetch_image_for_bounds(*rounded_tiles, zoom, multithread)
        arr = self._crop_to_bounds(image, *pixel_offsets)
        return RasterData(arr=arr)

    @property
    def value(self) -> np.ndarray:
        """Returns the value of a generated RasterData object.
        """
        return self.as_raster_data(self.zoom_levels[0],
                                   multithread=self.multithread).value

    def _get_simple_image_params(self,
                                 zoom) -> Tuple[float, float, float, float]:
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
        return (*[
            x * (2**(zoom)) / self.tile_size
            for x in [xstart, ystart, xend, yend]
        ],)

    def _get_3857_image_params(self, zoom) -> Tuple[float, float, float, float]:
        """Computes the x and y tile bounds for fetching an image that
        captures the entire labeling region (TiledData.bounds) given a specific zoom
        """
        lat_start, lat_end = self.tile_bounds.bounds[
            1].y, self.tile_bounds.bounds[0].y
        lng_start, lng_end = self.tile_bounds.bounds[
            1].x, self.tile_bounds.bounds[0].x

        # Convert to zoom 0 tile coordinates
        xstart, ystart = self._latlng_to_tile(lat_start, lng_start, zoom)
        xend, yend = self._latlng_to_tile(lat_end, lng_end, zoom)

        # Make sure that the tiles are increasing in order
        xstart, xend = min(xstart, xend), max(xstart, xend)
        ystart, yend = min(ystart, yend), max(ystart, yend)
        return (*[pt * 2.0**zoom for pt in [xstart, ystart, xend, yend]],)

    def _latlng_to_tile(self,
                        lat: float,
                        lng: float,
                        zoom=0) -> Tuple[float, float]:
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
        """Rounds a tile coordinate and reports the remainder in pixels
        """
        rounded_tile = int(tile)
        remainder = tile - rounded_tile
        pixel_offset = int(self.tile_size * remainder)
        return rounded_tile, pixel_offset

    def _fetch_image_for_bounds(self,
                                x_tile_start: int,
                                y_tile_start: int,
                                x_tile_end: int,
                                y_tile_end: int,
                                zoom: int,
                                multithread=True) -> np.ndarray:
        """Fetches the tiles and combines them into a single image
        """
        tiles = {}
        if multithread:
            with ThreadPoolExecutor(
                    max_workers=TILE_DOWNLOAD_CONCURRENCY) as exc:
                for x in range(x_tile_start, x_tile_end + 1):
                    for y in range(y_tile_start, y_tile_end + 1):
                        tiles[(x, y)] = exc.submit(self._fetch_tile, x, y, zoom)

            rows = []
            for y in range(y_tile_start, y_tile_end + 1):
                rows.append(
                    np.hstack([
                        tiles[(x, y)].result()
                        for x in range(x_tile_start, x_tile_end + 1)
                    ]))
        #no multithreading
        else:
            for x in range(x_tile_start, x_tile_end + 1):
                for y in range(y_tile_start, y_tile_end + 1):
                    tiles[(x, y)] = self._fetch_tile(x, y, zoom)

            rows = []
            for y in range(y_tile_start, y_tile_end + 1):
                rows.append(
                    np.hstack([
                        tiles[(x, y)]
                        for x in range(x_tile_start, x_tile_end + 1)
                    ]))

        return np.vstack(rows)

    @retry(delay=1, tries=6, backoff=2, max_delay=16)
    def _fetch_tile(self, x: int, y: int, z: int) -> np.ndarray:
        """
        Fetches the image and returns an np array. If the image cannot be fetched, 
        a padding of expected tile size is instead added.
        """
        try:
            data = requests.get(self.tile_layer.url.format(x=x, y=y, z=z))
            data.raise_for_status()
            decoded = np.array(Image.open(BytesIO(data.content)))[..., :3]
            if decoded.shape[:2] != (self.tile_size, self.tile_size):
                logger.warning(
                    f"Unexpected tile size {decoded.shape}. Results aren't guarenteed to be correct."
                )
        except:
            logger.warning(
                f"Unable to successfully find tile. for z,x,y: {z},{x},{y} "
                "Padding is being added as a result.")
            decoded = np.zeros(shape=(self.tile_size, self.tile_size, 3),
                               dtype=np.uint8)
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

    def _validate_num_tiles(self, xstart: float, ystart: float, xend: float,
                            yend: float, max_tiles: int):
        """Calculates the number of expected tiles we would fetch.

        If this is greater than the number of max tiles, raise an error.
        """
        total_n_tiles = (yend - ystart + 1) * (xend - xstart + 1)
        if total_n_tiles > max_tiles:
            raise ValueError(f"Requested zoom results in {total_n_tiles} tiles."
                             f"Max allowed tiles are {max_tiles}")

    @validator('zoom_levels')
    def validate_zoom_levels(cls, zoom_levels):
        if zoom_levels[0] > zoom_levels[1]:
            raise ValueError(
                f"Order of zoom levels should be min, max. Received {zoom_levels}"
            )
        return zoom_levels


#TODO: we will need to update the [data] package to also require pyproj
class EPSGTransformer(BaseModel):
    """Transformer class between different EPSG's. Useful when wanting to project
    in different formats.

    Requires as input a Point object.
    """

    class ProjectionTransformer(Transformer):
        """Custom class to help represent a Transformer that will play
        nicely with Pydantic.

        Accepts a PyProj Transformer object.
        """

        @classmethod
        def __get_validators__(cls):
            yield cls.validate

        @classmethod
        def validate(cls, v):
            if not isinstance(v, Transformer):
                raise Exception("Needs to be a Transformer class")
            return v

    transform_function: Optional[ProjectionTransformer] = None

    def _is_simple(self, epsg: EPSG) -> bool:
        return epsg == EPSG.SIMPLEPIXEL

    def geo_and_geo(self, src_epsg: EPSG, tgt_epsg: EPSG) -> None:
        if self._is_simple(src_epsg) or self._is_simple(tgt_epsg):
            raise Exception(
                f"Cannot be used for Simple transformations. Found {src_epsg} and {tgt_epsg}"
            )
        self.transform_function = Transformer.from_crs(src_epsg.value,
                                                       tgt_epsg.value)

    #TODO
    def geo_and_pixel(self, src_epsg, geojson):
        pass

    def __call__(self, point: Point):
        if self.transform_function is not None:
            res = self.transform_function.transform(point.x, point.y)
            return Point(x=res[0], y=res[1])
        else:
            raise Exception("No transformation has been set.")
