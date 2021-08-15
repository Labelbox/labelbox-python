from typing import List, Optional, Union, Tuple

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

    def draw(self,
             height: Optional[int] = None,
             width: Optional[int] = None,
             canvas: Optional[np.ndarray] = None,
             color: Union[int, Tuple[int, int, int]] = (255, 255, 255),
             thickness: int = -1) -> np.ndarray:
        """
        Draw the polygon onto a 3d mask
        Args:
            height (int): height of the mask
            width (int): width of the mask
            color (int): color for the polygon.
                  RGB values by default but if a 2D canvas is provided this can set this to an int.
            thickness (int): How thick to make the polygon border. -1 fills in the polygon
            canvas (np.ndarray): Canvas to draw the polygon on
        Returns:
            numpy array representing the mask with the polygon drawn on it.
        """
        canvas = self.get_or_create_canvas(height, width, canvas)
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
