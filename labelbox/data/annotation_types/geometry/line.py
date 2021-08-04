from typing import List, Optional, Union, Tuple

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
               height: Optional[int] = None,
               width: Optional[int] = None,
               thickness: int = 1,
               color: Union[Tuple, int] = (255, 255, 255),
               canvas: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Draw the line onto a 3d mask
        Args:
            height (int): height of the mask
            width (int): width of the mask
            thickness (int): How thick to draw the line
            color (int): color for the line.
                  RGB values by default but if a 2D canvas is provided this can set this to an int.
            canvas (np.ndarry): Canvas for drawing line on.
        Returns:
            numpy array representing the mask with the line drawn on it.
        """
<<<<<<< HEAD
        if canvas is None:
            canvas = np.zeros((height, width, 3), dtype=np.uint8)
=======
        canvas = self.get_or_create_canvas(height, width, canvas)
>>>>>>> 71d3643cdba268702cf5c796c6c43755750cd88c
        pts = np.array(self.geometry['coordinates']).astype(np.int32)
        return cv2.polylines(canvas,
                             pts,
                             False,
                             color=color,
                             thickness=thickness)
