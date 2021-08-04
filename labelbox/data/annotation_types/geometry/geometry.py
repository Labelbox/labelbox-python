from typing import Dict, Any, Optional, Union

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

    def raster(self, *args, **kwargs) -> np.ndarray:
        raise NotImplementedError("Subclass must override this")

    def get_or_create_canvas(self, height: Optional[int], width: Optional[int],
                             canvas: Optional[np.ndarray]) -> np.ndarray:
        if canvas is None:
            if height is None or width is None:
                raise ValueError(
                    "Must either provide canvas or height and width")
            canvas = np.zeros((height, width, 3), dtype=np.uint8)
        return canvas
