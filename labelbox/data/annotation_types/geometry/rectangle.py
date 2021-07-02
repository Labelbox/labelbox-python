

from labelbox.data.annotation_types.geometry.geometry import Geometry
import marshmallow_dataclass
from labelbox.data.annotation_types.marshmallow import required
import geojson
from typing import Dict, Any

@marshmallow_dataclass.dataclass
class Rectangle(Geometry):
    top: float = required()
    left: float = required()
    height: float = required()
    width: float = required()

    @property
    def geometry(self) -> geojson.geometry.Geometry:
        return geojson.MultiPolygon(
            [
                [
                    [
                        [self.left, self.top + self.height],
                        [self.left, self.top],
                        [self.left + self.width, self.top],
                        [self.left + self.width, self.top + self.height],
                        # close the polygon
                        [self.left, self.top + self.height],
                    ]
                ]
            ]
        )

    def to_mal_ndjson(self) -> Dict[str, Any]:
        return {
            "bbox" : {
                "top" : self.top,
                "left" : self.left,
                "height" : self.height,
                "width" : self.width,
            }
        }
