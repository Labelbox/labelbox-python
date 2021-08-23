from typing import Optional, Tuple, Union

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

    def draw(self,
             height: Optional[int] = None,
             width: Optional[int] = None,
             canvas: Optional[np.ndarray] = None,
             color: Union[int, Tuple[int, int, int]] = (255, 255, 255),
             thickness: int = 10) -> np.ndarray:
        """
        Draw the point onto a 3d mask
        Args:
            height (int): height of the mask
            width (int): width of the mask
            thickness (int): pixel radius of the point
            color (int): color for the point.
                  RGB values by default but if a 2D canvas is provided this can set this to an int.
            canvas (np.ndarray): Canvas to draw the point on
        Returns:
            numpy array representing the mask with the point drawn on it.
        """
        canvas = self.get_or_create_canvas(height, width, canvas)
        return cv2.circle(canvas, (int(self.x), int(self.y)),
                          radius=thickness,
                          color=color,
                          thickness=-1)
