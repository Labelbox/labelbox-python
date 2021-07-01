

from typing import List

from labelbox.data.annotation_types.geometry.point import Point
from labelbox.data.annotation_types.geometry.geometry import Geometry
from labelbox.data.annotation_types.marshmallow import required
import geojson
import marshmallow_dataclass


@marshmallow_dataclass.dataclass
class Polygon(Geometry):
    points: List[Point] = required()

    def geometry(self):
        if self.points[0] != self.points[-1]:
            self.points.append(self.points[0])
        return geojson.MultiPolygon([[[[point.x, point.y] for point in self.polygon]]])


