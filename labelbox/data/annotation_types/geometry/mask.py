from typing import Any, Dict, Tuple

import numpy as np
from labelbox.data.annotation_types.data.raster import RasterData
from labelbox.data.annotation_types.geometry.geometry import Geometry
from rasterio.features import shapes
from shapely.geometry import MultiPolygon, shape


class Mask(Geometry):
    # Raster data can be shared across multiple masks... or not
    mask: RasterData
    color_rgb: Tuple[int, int, int]

    @property
    def geometry(self):
        mask = self.mask.data
        mask = np.alltrue(mask == self.color_rgb, axis=2).astype(np.uint8)
        polygons = (
            shape(shp)
            for shp, val in shapes(mask, mask=None)
            # ignore if shape is area of smaller than 1 pixel
            if val >= 1)
        return MultiPolygon(polygons).__geo_interface__

    def raster(self) -> np.ndarray:
        return self.mask.data

    def create_url(self, signer):
        return self.mask.create_url(signer)
