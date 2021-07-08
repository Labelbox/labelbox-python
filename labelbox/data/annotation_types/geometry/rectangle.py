import geojson
from typing import Dict, Any
import numpy as np

from labelbox.data.annotation_types.geometry.geometry import Geometry
from labelbox.data.annotation_types.geometry.point import Point


class Rectangle(Geometry):
    start: Point
    end: Point

    @property
    def geometry(self) -> geojson.geometry.Geometry:
        return geojson.Polygon([[
            [self.start.x, self.start.y],
            [self.start.x, self.end.y],
            [self.end.x, self.end.y],
            [self.end.x, self.start.y],
            # close the polygon
            [self.start.x, self.start.y],
        ]])

    def raster(self, height: int, width: int) -> np.ndarray:
        canvas = np.zeros((height, width), dtype=np.uint8)
        raise NotImplementedError("")
        return



