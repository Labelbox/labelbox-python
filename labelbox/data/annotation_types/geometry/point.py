


from typing import List, Optional

from labelbox.data.annotation_types.geometry.geometry import Geometry
from labelbox.data.annotation_types.marshmallow import required
import geojson
import marshmallow_dataclass
import numpy as np


@marshmallow_dataclass.dataclass
class Point(Geometry):
    x: int = required()
    y: int = required()

    @property
    def geometry(self):
        return geojson.Point([self.x, self.y])

    def raster(self, height: int, width: int, point_buffer: Optional[int] = None):
        canvas = np.zeros((height, width), dtype = np.uint8)
        return canvas

    def to_mal_ndjson(self):
        return {
            'x' : self.x,
            'y' : self.y
        }
