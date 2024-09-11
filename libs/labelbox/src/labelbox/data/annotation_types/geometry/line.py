from typing import List, Optional, Union, Tuple

import geojson
import numpy as np
import cv2

from shapely.geometry import LineString as SLineString

from .point import Point
from .geometry import Geometry

from pydantic import field_validator


class Line(Geometry):
    """Line annotation

    Args:
        points (List[Point]): A list of `Point` geometries

    >>> Line(points = [Point(x=3,y=4), Point(x=3,y=5)])

    """

    points: List[Point]

    @property
    def geometry(self) -> geojson.MultiLineString:
        return geojson.MultiLineString(
            [[[point.x, point.y] for point in self.points]]
        )

    @classmethod
    def from_shapely(cls, shapely_obj: SLineString) -> "Line":
        """Transforms a shapely object."""
        if not isinstance(shapely_obj, SLineString):
            raise TypeError(
                f"Expected Shapely Line. Got {shapely_obj.geom_type}"
            )

        obj_coords = shapely_obj.__geo_interface__["coordinates"]
        return Line(
            points=[Point(x=coords[0], y=coords[1]) for coords in obj_coords]
        )

    def draw(
        self,
        height: Optional[int] = None,
        width: Optional[int] = None,
        canvas: Optional[np.ndarray] = None,
        color: Union[int, Tuple[int, int, int]] = (255, 255, 255),
        thickness: int = 1,
    ) -> np.ndarray:
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
        canvas = self.get_or_create_canvas(height, width, canvas)
        pts = np.array(self.geometry["coordinates"]).astype(np.int32)
        return cv2.polylines(
            canvas, pts, False, color=color, thickness=thickness
        )

    @field_validator("points")
    def is_geom_valid(cls, points):
        if len(points) < 2:
            raise ValueError(
                f"A line must have at least 2 points to be valid. Found {points}"
            )

        return points
