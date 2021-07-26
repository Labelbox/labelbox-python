import cv2
import geojson
import numpy as np

from .geometry import Geometry
from .point import Point


class Rectangle(Geometry):
    """
    Represents a 2d rectangle. Also known as a bounding box.

    start: Top left coordinate of the rectangle
    end: Bottom right coordinate of the rectangle
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

    def raster(self, height: int, width: int,
               color=(255, 255, 255)) -> np.ndarray:
        """
        Draw the rectangle onto a 3d mask

        Args:
            height (int): height of the mask
            width (int): width of the mask
            color (int): color for the rectangle. Only a single int since this is a grayscale mask.
        Returns:
            numpy array representing the mask with the rectangle drawn on it.
        """
        canvas = np.zeros((height, width, 3), dtype=np.uint8)
        pts = np.array(self.geometry['coordinates']).astype(np.int32)
        return cv2.fillPoly(canvas, pts=pts, color=color)
