from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, validator, conlist
import numpy as np
from pyproj import Transformer

from ..geometry import Point
from .base_data import BaseData
from .raster import RasterData


class EPSG(Enum):
    """ Provides the EPSG for tiled image assets that are currently supported.
    
    SIMPLEPIXEL is Simple that can be used to obtain the pixel space coordinates

    >>> epsg = EPSG()
    """
    SIMPLEPIXEL = 1
    EPSG4326 = 4326
    EPSG3857 = 3857
    EPSG3395 = 3395


class TiledBounds(BaseModel):
    """ Bounds for a tiled image asset related to the relevant epsg. 

    Bounds should be Point objects

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
    def validate_bounds(cls, bounds):
        first_bound = bounds[0]
        second_bound = bounds[1]

        if first_bound == second_bound:
            raise AssertionError(f"Bounds cannot be equal, contains {bounds}")
        return bounds


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
            raise AssertionError(f"{url} needs to contain {xyz_format}")
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
    """
    tile_layer: TileLayer
    tile_bounds: TiledBounds
    alternative_layers: List[TileLayer] = None
    zoom_levels: conlist(item_type=int, min_items=2, max_items=2)
    max_native_zoom: int = None
    tile_size: Optional[int]
    version: int = 2

    #TODO: look further into Matt's code and how to reference the monorepo ?
    def _as_raster(zoom):
        # stitched together tiles as a RasterData object
        # TileData.get_image(target_hw) ← we will be using this from Matt's precomputed embeddings
        # more info found here: https://github.com/Labelbox/python-monorepo/blob/baac09cb89e083209644c9bdf1bc3d7cb218f147/services/precomputed_embeddings/precomputed_embeddings/tiled.py
        image_as_np = None
        return RasterData(arr=image_as_np)

    #TODO
    @property
    def value(self) -> np.ndarray:
        return self._as_raster(self.min_zoom).value()


#TODO: we will need to update the [data] package to also require pyproj
class EPSGTransformer(BaseModel):
    """Transformer class between different EPSG's. Useful when wanting to project
    in different formats.

    Requires as input a Point object.
    """
    class ProjectionTransformer():
        """Custom class to help represent a Transformer that will play
        nicely with Pydantic.
        """
        @classmethod
        def __get_validators__(cls):
            yield cls.validate

        @classmethod
        def validate(cls, v):
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
