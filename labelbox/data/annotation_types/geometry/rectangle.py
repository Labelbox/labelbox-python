

from labelbox.data.annotation_types.geometry.geometry import Geometry
import marshmallow_dataclass
from labelbox.data.annotation_types.marshmallow import required
import geojson

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
