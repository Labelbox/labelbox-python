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
               color=(255, 255, 255)) -> np.ndarray:
        """
        Draw the line onto a 3d mask

        Args:
            height (int): height of the mask
            width (int): width of the mask
            thickness (int): How thick to draw the line
            color (int): color for the line. Only a single int since this is a grayscale mask.
        Returns:
            numpy array representing the mask with the line drawn on it.
        """
        canvas = np.zeros((height, width, 3), dtype=np.uint8)
        pts = np.array(self.geometry['coordinates']).astype(np.int32)
        return cv2.polylines(canvas,
                             pts,
                             False,
                             color=color,
                             thickness=thickness)
