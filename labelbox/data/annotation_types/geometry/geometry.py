
from labelbox.data.annotation_types.annotation import Annotation
from shapely.geomtry import shape
import geojson
import marshmallow_dataclass
from typing import Dict, Any

@marshmallow_dataclass.dataclass
class Geometry:
    @property
    def geometry(self) -> geojson:
        raise NotImplementedError("Subclass must override this")

    @property
    def shapely(self):
        return shape(self.geometry)


    def raster(self, height: int, width: int):
        raise NotImplementedError("Subclass must override this")

    def to_mal_ndjson(self) -> Dict[str, Any]:
        raise NotImplementedError("Subclass must override this")



