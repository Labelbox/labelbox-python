from typing import List

import geojson
import numpy as np
import cv2

from .point import Point
from .geometry import Geometry


class Line(Geometry):
    points: List[Point]

    @property
    def geometry(self) -> geojson.MultiLineString:
        return geojson.MultiLineString(
            [[[point.x, point.y] for point in self.points]])

    def raster(self,
               height: int,
               width: int,
               thickness=1,
               color=255) -> np.ndarray:

        canvas = np.zeros((height, width), dtype=np.uint8)
        pts = np.array(self.geometry['coordinates']).astype(np.int32)
        return cv2.polylines(canvas,
                             pts,
                             False,
                             color=color,
                             thickness=thickness)
