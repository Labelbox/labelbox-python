import geojson
from typing import Dict, Any
import numpy as np

from labelbox.data.annotation_types.geometry.geometry import Geometry


class Rectangle(Geometry):
    top: float
    left: float
    height: float
    width: float

    @property
    def geometry(self) -> geojson.geometry.Geometry:
        return geojson.MultiPolygon([[[
            [self.left, self.top + self.height],
            [self.left, self.top],
            [self.left + self.width, self.top],
            [self.left + self.width, self.top + self.height],
            # close the polygon
            [self.left, self.top + self.height],
        ]]])


    def raster(self, height: int, width: int) -> np.ndarray:
        canvas = np.zeros((height, width), dtype=np.uint8)
        raise NotImplementedError("")
        return
