

from rasterio.features import shapes
from labelbox.data.annotation_types.geometry.geometry import Geometry
from labelbox.data.annotation_types.data.raster import RasterData
from labelbox.data.annotation_types.marshmallow import default_none
import marshmallow_dataclass
from shapely.geometry import MultiPolygon, shape
from labelbox.data.annotation_types.marshmallow import required
from functools import cached_property

@marshmallow_dataclass.dataclass
class Mask(Geometry):
    mask: RasterData = required()

    @cached_property
    def geometry(self):
        mask = self.mask.numpy
        if len(mask.shape) != 2:
            raise ValueError(
                "Mask must be 2d mask. Save each channel as a separate Annotation"
        )
        mask = mask > 0
        polygons = (
            shape(shp)
        for shp, val in shapes(mask, mask=None)
        # ignore if shape is area of smaller than 1 pixel
        if val >= 1
        )
        return MultiPolygon(polygons).__geo_interface__
