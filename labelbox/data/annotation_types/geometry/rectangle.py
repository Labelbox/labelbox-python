from typing import Optional, Union, Tuple

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

    def raster(self,
               height: Optional[int] = None,
               width: Optional[int] = None,
               color: Union[int, Tuple] = (255, 255, 255),
               thickness: int = -1,
               canvas: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Draw the rectangle onto a 3d mask
        Args:
            height (int): height of the mask
            width (int): width of the mask
            color (int): color for the polygon.
                  RGB values by default but if a 2D canvas is provided this can set this to an int.
            thickness (int): How thick to make the rectangle border. -1 fills in the rectangle
            canvas (np.ndarray): Canvas to draw rectangle on
        Returns:
            numpy array representing the mask with the rectangle drawn on it.
        """
        canvas = self.get_or_create_canvas(height, width, canvas)
        pts = np.array(self.geometry['coordinates']).astype(np.int32)
        if thickness == -1:
            return cv2.fillPoly(canvas, pts, color)
        return cv2.polylines(canvas, pts, True, color, thickness)
