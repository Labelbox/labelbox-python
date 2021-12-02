from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, validator

from .geometry import Point


class EPSG(Enum):
    """ Provides the EPSG for tiled image assets that are currently supported.
    
    SIMPLEPIXEL is Simple that can be used to obtain the pixel space coordinates

    >>> epsg = EPSG()
    """
    SIMPLEPIXEL = 1
    EPSG4326 = 2
    EPSG3857 = 3
    EPSG3395 = 4


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
