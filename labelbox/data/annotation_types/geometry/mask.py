from typing import Callable, Tuple

import numpy as np
from rasterio.features import shapes
from shapely.geometry import MultiPolygon, shape

from ..data.raster import RasterData
from .geometry import Geometry


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

    def create_url(self, signer: Callable[[bytes], str]) -> str:
        """
        Update the segmentation mask to have a url.
        Only update the mask if it doesn't already have a url

        Args:
            signer: A function that accepts bytes and returns a signed url.
        Returns:
            the url for the mask
        """
        return self.mask.create_url(signer)
