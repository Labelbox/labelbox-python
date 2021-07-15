

from labelbox.data.annotation_types.classification.classification import Subclass
from labelbox.data.annotation_types.geometry.line import Line
from labelbox.data.annotation_types.geometry.point import Point
from labelbox.data.annotation_types.geometry.polygon import Polygon
from labelbox.data.annotation_types.geometry.rectangle import Rectangle
from labelbox.data.annotation_types.geometry.mask import Mask
from labelbox.data.annotation_types.data.raster import RasterData
from labelbox.data.serialization.labelbox_v1 import classifications
from labelbox.data.serialization.labelbox_v1.feature import LBV1Feature
from labelbox.data.serialization.labelbox_v1.classifications import LBV1Radio, LBV1Checklist, LBV1Text
from pydantic import BaseModel
from typing import List, Optional, Union, Any


class LBV1ObjectBase(LBV1Feature):
    color: Optional[str] = None
    instanceURI: Optional[str] = None
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

    def to_common(self) -> Rectangle:
        return Rectangle(start=Point(x=self.left, y=self.top),
                           end=Point(x=self.left + self.width,
                                     y=self.top + self.height))

    @classmethod
    def from_common(cls, rectangle : Rectangle, classifications: List[Subclass]) -> "LBV1Rectangle":
        return cls(
            bbox = BoxLocation(
                top = rectangle.start.y,
                left = rectangle.start.x,
                height = rectangle.end.y - rectangle.start.y,
                width = rectangle.end.x - rectangle.start.x,
            ),
            classifications = classifications
        )



class LBV1Polygon(LBV1ObjectBase):
    polygon: List[PointLocation]

    def to_common(self) -> Polygon:
        return Line(points=[Point(x=p.x, y=p.y) for p in self.polygon])


    @classmethod
    def from_common(cls, polygon : Polygon, classifications: List[Subclass]) -> "LBV1Polygon":
        return cls(
            polygon = [PointLocation(x = point.x, y = point.y) for point in polygon.points],
            classifications = classifications
        )


class LBV1Point(LBV1ObjectBase):
    point: PointLocation

    def to_common(self) -> Point:
        return Point(x=self.point.x, y=self.point.y)

    @classmethod
    def from_common(cls, point : Point, classifications: List[Subclass]) -> "LBV1Point":
        return cls(
            point = PointLocation(x = point.x, y = point.y),
            classifications = classifications
        )



class LBV1Line(LBV1ObjectBase):
    line: List[PointLocation]

    def to_common(self):
        return Line(points=[Point(x=p.x, y=p.y) for p in self.line])

    @classmethod
    def from_common(cls, polygon : Line, classifications: List[Subclass]) -> "LBV1Line":
        return cls(
            line = [PointLocation(x = point.x, y = point.y) for point in polygon.points],
            classifications = classifications
        )


class LBV1Mask(LBV1ObjectBase):
    instanceURI: str

    def to_common(self):
        return Mask(
            mask=RasterData(url=self.instanceURI), color_rgb=(255, 255, 255))

    @classmethod
    def from_common(cls, mask : Mask, classifications: List[Subclass]) -> "LBV1Line":
        return cls(
            instanceURI = mask.url,
            classifications = classifications
        )


LBV1Object = Union[LBV1Line, LBV1Point, LBV1Polygon, LBV1Rectangle, LBV1Mask]

#LBV1Label(**data.json()[0])
#LBV1Label(**data.json()[0]).dict(by_alias=True)
