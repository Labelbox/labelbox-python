
from labelbox.data.annotation_types.annotation import Annotation
from shapely.geomtry import shape
import geojson
import marshmallow_dataclass

@marshmallow_dataclass.dataclass
class Geometry:
    @property
    def geometry(self) -> geojson:
        raise NotImplementedError("Subclass must override this")

    @property
    def shapely(self):
        return shape(self.geometry)
