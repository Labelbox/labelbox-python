from typing import Dict, Any, Union

import geojson
import numpy as np
from shapely import geometry as geom
from pydantic import BaseModel


class Geometry(BaseModel):
    """
    Base class for geometry objects. Shouldn't be directly instantiated.
    """
    extra: Dict[str, Any] = {}

    @property
    def geometry(self) -> geojson:
        raise NotImplementedError("Subclass must override this")

    @property
    def shapely(
        self
    ) -> Union[geom.Point, geom.LineString, geom.Polygon, geom.MultiPoint,
               geom.MultiLineString, geom.MultiPolygon]:
        return geom.shape(self.geometry)

    def raster(self, height: int, width: int) -> np.ndarray:
        raise NotImplementedError("Subclass must override this")
