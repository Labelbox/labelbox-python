


from typing import List

from labelbox.data.annotation_types.geometry.geometry import Geometry
from labelbox.data.annotation_types.marshmallow import required
import geojson
import marshmallow_dataclass


@marshmallow_dataclass.dataclass
class Point(Geometry):
    x: int = required()
    y: int = required()

    @property
    def geometry(self):
        return geojson.Point([self.x, self.y])

