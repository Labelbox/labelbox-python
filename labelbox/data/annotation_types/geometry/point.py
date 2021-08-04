from typing import Optional

import geojson
import numpy as np
import cv2

from .geometry import Geometry


class Point(Geometry):
    x: float
    y: float

    @property
    def geometry(self) -> geojson.Point:
        return geojson.Point([self.x, self.y])

    def raster(self,
               height: Optional[int] = None,
               width: Optional[int] = None,
               thickness: int = 1,
               color=(255, 255, 255),
               canvas=None) -> np.ndarray:
        """
        Draw the point onto a 3d mask
        Args:
            height (int): height of the mask
            width (int): width of the mask
            thickness (int): pixel radius of the point
            color (int): color for the point. Only a single int since this is a grayscale mask.
        Returns:
            numpy array representing the mask with the point drawn on it.
        """
        if canvas is None:
            if height is None or width is None:
                raise ValueError(
                    "Must either provide canvas or height and width")
            canvas = np.zeros((height, width, 3), dtype=np.uint8)
        return cv2.circle(canvas, (int(self.x), int(self.y)),
                          radius=thickness,
                          color=color,
                          thickness=-1)
