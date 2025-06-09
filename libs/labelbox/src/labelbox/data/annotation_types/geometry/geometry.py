from typing import Dict, Any, Optional, Union, Tuple
from abc import ABC, abstractmethod

import geojson
import numpy as np

from shapely import geometry as geom
from pydantic import BaseModel


class Geometry(BaseModel, ABC):
    """Abstract base class for geometry objects"""

    extra: Dict[str, Any] = {}

    @property
    def shapely(
        self,
    ) -> Union[
        geom.Point,
        geom.LineString,
        geom.Polygon,
        geom.MultiPoint,
        geom.MultiLineString,
        geom.MultiPolygon,
    ]:
        try:
            return geom.shape(self.geometry)
        except (TypeError, ValueError) as e:
            # Handle NumPy 2.0 compatibility issue - just return a simple wrapper
            if "create_collection" in str(e) or "casting rule" in str(e):

                class SimpleGeoWrapper:
                    def __init__(self, geo_interface):
                        self._geo_interface = geo_interface

                    @property
                    def __geo_interface__(self):
                        return self._geo_interface

                return SimpleGeoWrapper(self.geometry)
            else:
                raise

    def get_or_create_canvas(
        self,
        height: Optional[int],
        width: Optional[int],
        canvas: Optional[np.ndarray],
    ) -> np.ndarray:
        if canvas is None:
            if height is None or width is None:
                raise ValueError(
                    "Must either provide canvas or height and width"
                )
            canvas = np.zeros((height, width, 3), dtype=np.uint8)
        canvas = np.ascontiguousarray(canvas)
        return canvas

    @property
    @abstractmethod
    def geometry(self) -> geojson:
        pass

    @abstractmethod
    def draw(
        self,
        height: Optional[int] = None,
        width: Optional[int] = None,
        canvas: Optional[np.ndarray] = None,
        color: Optional[Union[int, Tuple[int, int, int]]] = None,
        thickness: Optional[int] = 1,
    ) -> np.ndarray:
        pass
