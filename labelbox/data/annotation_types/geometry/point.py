from typing import Dict, Optional

import cv2

from labelbox.data.annotation_types.geometry.geometry import Geometry

import geojson
import numpy as np


class Point(Geometry):
    x: float
    y: float

    @property
    def geometry(self) -> geojson.Point:
        return geojson.Point([self.x, self.y])

    def raster(self,
               height: int,
               width: int,
               thickness: int = 1,
               color=255) -> np.ndarray:
        canvas = np.zeros((height, width), dtype=np.uint8)
        return cv2.circle(canvas, (int(self.x), int(self.y)),
                          radius=thickness,
                          color=color,
                          thickness=-1)
