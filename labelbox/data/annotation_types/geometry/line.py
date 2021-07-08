from typing import List, Optional, Dict, Any

import geojson
import numpy as np
import cv2

from labelbox.data.annotation_types.geometry.point import Point
from labelbox.data.annotation_types.geometry.geometry import Geometry


class Line(Geometry):
    points: List[Point]

    @property
    def geometry(self) -> geojson.MultiLineString:
        return geojson.MultiLineString(
            [[[point.x, point.y] for point in self.points]])

    def raster(self,
               height: int,
               width: int,
               line_buffer: Optional[int] = None) -> np.ndarray:
        canvas = np.zeros((height, width), dtype=np.uint8)

        raise NotImplementedError("")
        return canvas
