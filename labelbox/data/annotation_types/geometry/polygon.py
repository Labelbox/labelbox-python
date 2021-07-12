from typing import Any, Dict, List

import numpy as np
import geojson
import cv2
from pydantic import ValidationError, validator

from labelbox.data.annotation_types.geometry.point import Point
from labelbox.data.annotation_types.geometry.geometry import Geometry


class Polygon(Geometry):
    points: List[Point]

    @property
    def geometry(self) -> geojson.MultiPolygon:
        if self.points[0] != self.points[-1]:
            self.points.append(self.points[0])
        return geojson.Polygon([[[point.x, point.y] for point in self.points]])

    def raster(self, height: int, width: int, color=255) -> np.ndarray:
        canvas = np.zeros((height, width), dtype=np.uint8)
        pts = np.array(self.geometry['coordinates']).astype(np.int32)
        return cv2.fillPoly(canvas, pts=pts, color=color)

    @validator('points')
    def is_geom_valid(cls, points):
        if len(points) < 3:
            raise ValidationError(
                f"A polygon must have at least 3 points to be valid. Found {points}"
            )
        return points
