
from typing import List

from labelbox.data.annotation_types.marshmallow import required
from labelbox.data.annotation_types.geometry.point import Point
from labelbox.data.annotation_types.geometry.geometry import Geometry
import geojson
import marshmallow_dataclass

@marshmallow_dataclass.dataclass
class Line(Geometry):
    line: List[Point] = required()

    @property
    def geometry(self):
        return geojson.MultiLineString([[[point.x, point.y] for point in self.line]])




