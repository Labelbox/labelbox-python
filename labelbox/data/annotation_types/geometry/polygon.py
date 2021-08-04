from typing import List, Optional

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

    def raster(self,
               height: Optional[int] = None,
               width: Optional[int] = None,
               color=(255, 255, 255),
               thickness=-1,
               canvas=None) -> np.ndarray:
        """
        Draw the polygon onto a 3d mask
        Args:
            height (int): height of the mask
            width (int): width of the mask
            color (int): color for the polygon. Only a single int since this is a grayscale mask.
        Returns:
            numpy array representing the mask with the polygon drawn on it.
        """
        if canvas is None:
            if height is None or width is None:
                raise ValueError(
                    "Must either provide canvas or height and width")
            canvas = np.zeros((height, width, 3), dtype=np.uint8)
        pts = np.array(self.geometry['coordinates']).astype(np.int32)
        if thickness == -1:
            return cv2.fillPoly(canvas, pts, color)
        return cv2.polylines(canvas, pts, True, color, thickness)

    @validator('points')
    def is_geom_valid(cls, points):
        if len(points) < 3:
            raise ValueError(
                f"A polygon must have at least 3 points to be valid. Found {points}"
            )
        return points
