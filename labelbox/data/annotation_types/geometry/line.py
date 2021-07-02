
from typing import List, Optional

from labelbox.data.annotation_types.marshmallow import required
from labelbox.data.annotation_types.geometry.point import Point
from labelbox.data.annotation_types.geometry.geometry import Geometry
import geojson
import marshmallow_dataclass
import numpy as np
from typing import Dict, Any

@marshmallow_dataclass.dataclass
class Line(Geometry):
    points: List[Point] = required()

    @property
    def geometry(self):
        return geojson.MultiLineString([[[point.x, point.y] for point in self.line]])

    def raster(self, height: int, width: int, line_buffer: Optional[int] = None):
        canvas = np.zeros((height, width), dtype = np.uint8)
        return canvas

    def to_mal_ndjson(self) -> Dict[str, Any]:
        return {
            "line" : [point.to_mal_ndjson() for point in self.points]
        }



