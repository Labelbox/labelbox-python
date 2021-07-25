from typing import List

import numpy as np
import geojson
import cv2
from pydantic import validator

from .point import Point
from .geometry import Geometry


class Polygon(Geometry):
    points: List[Point]

    @property
    def geometry(self) -> geojson.MultiPolygon:
        if self.points[0] != self.points[-1]:
            self.points.append(self.points[0])
        return geojson.Polygon([[[point.x, point.y] for point in self.points]])

    def raster(self, height: int, width: int,
               color=(255, 255, 255)) -> np.ndarray:
        """
        Draw the polygon onto a 3d mask

        Args:
            height (int): height of the mask
            width (int): width of the mask
            color (int): color for the polygon. Only a single int since this is a grayscale mask.
        Returns:
            numpy array representing the mask with the polygon drawn on it.
        """
        canvas = np.zeros((height, width, 3), dtype=np.uint8)
        pts = np.array(self.geometry['coordinates']).astype(np.int32)
        return cv2.fillPoly(canvas, pts=pts, color=color)

    @validator('points')
    def is_geom_valid(cls, points):
        if len(points) < 3:
            raise ValueError(
                f"A polygon must have at least 3 points to be valid. Found {points}"
            )
        return points
