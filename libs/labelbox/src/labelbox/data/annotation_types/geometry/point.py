from typing import Optional, Tuple, Union

import geojson
import numpy as np
import cv2
from shapely.geometry import Point as SPoint

from .geometry import Geometry


class Point(Geometry):
    """Point geometry

    >>> Point(x=0, y=0)

    Args:
        x (float)
        y (float)

    """
    x: float
    y: float

    @property
    def geometry(self) -> geojson.Point:
        return geojson.Point((self.x, self.y))

    @classmethod
    def from_shapely(cls, shapely_obj: SPoint) -> "Point":
        """Transforms a shapely object."""
        if not isinstance(shapely_obj, SPoint):
            raise TypeError(
                f"Expected Shapely Point. Got {shapely_obj.geom_type}")

        obj_coords = shapely_obj.__geo_interface__['coordinates']
        return Point(x=obj_coords[0], y=obj_coords[1])

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
