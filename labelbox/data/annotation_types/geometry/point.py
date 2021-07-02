


from typing import Dict, Optional

from labelbox.data.annotation_types.geometry.geometry import Geometry
from labelbox.data.annotation_types.marshmallow import required
import geojson
import marshmallow_dataclass
import numpy as np


@marshmallow_dataclass.dataclass
class Point(Geometry):
    x: float = required()
    y: float = required()

    @property
    def geometry(self) -> geojson.Point:
        return geojson.Point([self.x, self.y])

    def raster(self, height: int, width: int, point_buffer: Optional[int] = None) -> np.ndarray:
        canvas = np.zeros((height, width), dtype = np.uint8)
        raise NotImplementedError("")
        return canvas

    def to_mal_ndjson(self) -> Dict[str, float]:
        return {
            'x' : self.x,
            'y' : self.y
        }
