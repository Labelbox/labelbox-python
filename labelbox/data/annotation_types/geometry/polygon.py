

from typing import List

from labelbox.data.annotation_types.geometry.point import Point
from labelbox.data.annotation_types.geometry.geometry import Geometry
from labelbox.data.annotation_types.marshmallow import required
import numpy as np
import geojson
import marshmallow_dataclass


@marshmallow_dataclass.dataclass
class Polygon(Geometry):
    points: List[Point] = required()

    @property
    def geometry(self):
        if self.points[0] != self.points[-1]:
            self.points.append(self.points[0])
        return geojson.MultiPolygon([[[[point.x, point.y] for point in self.polygon]]])

    def raster(self, height: int, width: int):
        canvas = np.zeros((height, width), dtype = np.uint8)
        return

    def to_mal_ndjson(self):
        return {
            "polygon" : [point.to_mal_ndjson() for point in self.points]
        }
