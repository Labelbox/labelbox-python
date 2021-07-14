from labelbox.data.annotation_types.geometry.line import Line
from labelbox.data.annotation_types.geometry.point import Point
from labelbox.data.annotation_types.data.raster import RasterData
from labelbox.data.annotation_types.geometry.mask import Mask
from labelbox.data.serialization.labelbox_v1.feature import LBV1Feature
from labelbox.data.serialization.labelbox_v1.classifications import LBV1Radio, LBV1Checklist, LBV1Text
from pydantic import BaseModel
from typing import List, Union, Any


class LBV1ObjectBase(LBV1Feature):
    color: str
    instanceURI: str
    classifications: List[Union[LBV1Radio, LBV1Checklist, LBV1Text]] = []


class PointLocation(BaseModel):
    x: float
    y: float


class BoxLocation(BaseModel):
    top: float
    left: float
    height: float
    width: float


class LBV1Rectangle(LBV1ObjectBase):
    bbox: BoxLocation

    def to_common(self):
        return BoxLocation(start=Point(x=self.left, y=self.top),
                           end=Point(x=self.left + self.width,
                                     y=self.top + self.height))


class LBV1Polygon(LBV1ObjectBase):
    polygon: List[PointLocation]

    def to_common(self):
        return Line(points=[Point(x=p.x, y=p.y) for p in self.polygon])


class LBV1Point(LBV1ObjectBase):
    point: PointLocation

    def to_common(self):
        return Point(x=self.point.x, y=self.point.y)


class LBV1Line(LBV1ObjectBase):
    line: List[PointLocation]

    def to_common(self):
        return Line(points=[Point(x=p.x, y=p.y) for p in self.line])


class LBV1Mask(LBV1ObjectBase):

    def to_common(self):
        return Mask(
            mask=RasterData(url=self.instanceURI, color_rgb=(255, 255, 255)))


LBV1Object = Union[LBV1Line, LBV1Point, LBV1Polygon, LBV1Rectangle, LBV1Mask]

#LBV1Label(**data.json()[0])
#LBV1Label(**data.json()[0]).dict(by_alias=True)
