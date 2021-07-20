from typing import Any, Dict

import cv2
import geojson
import numpy as np
from .geometry import Geometry
from .point import Point


class Rectangle(Geometry):
    """
    Represents a 2d rectangle. Also known as a bounding box.
    """
    start: Point
    end: Point

    @property
    def geometry(self) -> geojson.geometry.Geometry:
        return geojson.Polygon([[
            [self.start.x, self.start.y],
            [self.start.x, self.end.y],
            [self.end.x, self.end.y],
            [self.end.x, self.start.y],
            [self.start.x, self.start.y],
        ]])

    def raster(self, height: int, width: int, color: int = 255) -> np.ndarray:
        """
        Draw the rectangle onto a 2d mask

        Args:
            height (int): height of the mask
            width (int): width of the mask
            color (int): color for the rectangle. Only a single int since this is a grayscale mask.
        Returns:
            numpy array representing the mask with the rectangle drawn on it.
        """
        canvas = np.zeros((height, width), dtype=np.uint8)
        pts = np.array(self.geometry['coordinates']).astype(np.int32)
        return cv2.fillPoly(canvas, pts=pts, color=color)

    # TODO: Validate the start points are less than the end points
