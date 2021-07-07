from typing import Any, Callable, Dict, Tuple

import numpy as np
from rasterio.features import shapes
from shapely.geometry import MultiPolygon, shape

from labelbox.data.annotation_types.geometry.geometry import Geometry
from labelbox.data.annotation_types.data.raster import RasterData


class Mask(Geometry):
    # Raster data can be shared across multiple masks... or not
    mask: RasterData
    color_rgb: Tuple[int, int, int]

    @property
    def geometry(self):
        mask = self.mask.numpy
        mask = np.alltrue(mask == self.color_rgb, axis=2)
        polygons = (
            shape(shp)
            for shp, val in shapes(mask, mask=None)
            # ignore if shape is area of smaller than 1 pixel
            if val >= 1)
        return MultiPolygon(polygons).__geo_interface__

    def raster(self, height: int = None, width: int = None) -> np.ndarray:
        # TODO: maybe resize with height and width or pad...
        raise NotImplementedError("")
        return self.mask.numpy

    def upload_mask(self, signer: Callable[[np.ndarray], str]) -> None:
        # Only needs to be uploaded once across all references to this mask
        if self.mask.url is not None:
            return self.mask.url
        self.mask.url = signer(self.mask)

