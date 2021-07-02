

from typing import Any, Dict, List

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
    def geometry(self) -> geojson.MultiPolygon:
        if self.points[0] != self.points[-1]:
            self.points.append(self.points[0])
        return geojson.MultiPolygon([[[[point.x, point.y] for point in self.polygon]]])

    def raster(self, height: int, width: int) -> np.ndarray:
        canvas = np.zeros((height, width), dtype = np.uint8)
        raise NotImplementedError("")
        return

    def to_mal_ndjson(self) -> Dict[str, Any]:
        return {
            "polygon" : [point.to_mal_ndjson() for point in self.points]
        }
