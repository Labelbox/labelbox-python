from typing import Dict, Any, Union

import geojson
import numpy as np
from shapely import geometry as geom
from marshmallow_dataclass import dataclass

from labelbox.data.annotation_types.marshmallow import RequiredFieldMixin

@dataclass
class Geometry(RequiredFieldMixin):
    @property
    def geometry(self) -> geojson:
        raise NotImplementedError("Subclass must override this")

    @property
    def shapely(self) -> Union[geom.Point, geom.LineString, geom.Polygon, geom.MultiPoint, geom.MultiLineString, geom.MultiPolygon]:
        return geom.shape(self.geometry)

    def raster(self, height: int, width: int) -> np.ndarray:
        raise NotImplementedError("Subclass must override this")

    def to_mal_ndjson(self) -> Dict[str, Any]:
        raise NotImplementedError("Subclass must override this")



