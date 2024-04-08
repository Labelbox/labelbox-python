from typing import Optional, Union, Tuple
from enum import Enum

import cv2
import geojson
import numpy as np

from shapely.geometry import Polygon as SPolygon

from .geometry import Geometry
from .point import Point


class Rectangle(Geometry):
    """Represents a 2d rectangle. Also known as a bounding box

    >>> Rectangle(start=Point(x=0, y=0), end=Point(x=1, y=1))

    Args:
        start (Point): Top left coordinate of the rectangle
        end (Point): Bottom right coordinate of the rectangle
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

    @classmethod
    def from_shapely(cls, shapely_obj: SPolygon) -> "Rectangle":
        """Transforms a shapely object.
        
        If the provided shape is a non-rectangular polygon, a rectangle will be
        returned based on the min and max x,y values."""
        if not isinstance(shapely_obj, SPolygon):
            raise TypeError(
                f"Expected Shapely Polygon. Got {shapely_obj.geom_type}")

        min_x, min_y, max_x, max_y = shapely_obj.bounds

        start = [min_x, min_y]
        end = [max_x, max_y]

        return Rectangle(start=Point(x=start[0], y=start[1]),
                         end=Point(x=end[0], y=end[1]))

    def draw(self,
             height: Optional[int] = None,
             width: Optional[int] = None,
             canvas: Optional[np.ndarray] = None,
             color: Union[int, Tuple[int, int, int]] = (255, 255, 255),
             thickness: int = -1) -> np.ndarray:
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

    @classmethod
    def from_xyhw(cls, x: float, y: float, h: float, w: float) -> "Rectangle":
        """Create Rectangle from x,y, height width format"""
        return cls(start=Point(x=x, y=y), end=Point(x=x + w, y=y + h))


class RectangleUnit(Enum):
    INCHES = 'INCHES'
    PIXELS = 'PIXELS'
    POINTS = 'POINTS'


class DocumentRectangle(Rectangle):
    """Represents a 2d rectangle on a Document

    >>> Rectangle(
    >>>     start=Point(x=0, y=0),
    >>>     end=Point(x=1, y=1),
    >>>     page=4,
    >>>     unit=RectangleUnits.POINTS
    >>> )

    Args:
        start (Point): Top left coordinate of the rectangle
        end (Point): Bottom right coordinate of the rectangle
        page (int): Page number of the document
        unit (RectangleUnits): Units of the rectangle
    """
    page: int
    unit: RectangleUnit
