from typing import Any, List, Optional, Union

from labelbox.data.annotation_types.annotation import (
    AnnotationType, ClassificationAnnotation, ObjectAnnotation)
from labelbox.data.annotation_types.data.raster import RasterData
from labelbox.data.annotation_types.geometry.line import Line
from labelbox.data.annotation_types.geometry.mask import Mask
from labelbox.data.annotation_types.geometry.point import Point
from labelbox.data.annotation_types.geometry.polygon import Polygon
from labelbox.data.annotation_types.geometry.rectangle import Rectangle
from labelbox.data.annotation_types.ner import TextEntity
from labelbox.data.serialization.labelbox_v1.classifications import (
    LBV1Checklist, LBV1Classifications, LBV1Radio, LBV1Text)
from labelbox.data.serialization.labelbox_v1.feature import LBV1Feature
from pydantic import BaseModel


class LBV1ObjectBase(LBV1Feature):
    color: Optional[str] = None
    instanceURI: Optional[str] = None
    classifications: List[Union[LBV1Radio, LBV1Checklist, LBV1Text]] = []

    def dict(self, *args, **kwargs):
        res = super().dict(*args, **kwargs)
        # This means these are not video frames ..
        if self.instanceURI is None:
            res.pop('instanceURI')
        return res


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
        return Rectangle(start=Point(x=self.bbox.left, y=self.bbox.top),
                         end=Point(x=self.bbox.left + self.bbox.width,
                                   y=self.bbox.top + self.bbox.height))

    @classmethod
    def from_common(cls, rectangle: Rectangle,
                    classifications: List[ClassificationAnnotation],
                    schema_id: str, title: str, extra) -> "LBV1Rectangle":
        return cls(bbox=BoxLocation(
            top=rectangle.start.y,
            left=rectangle.start.x,
            height=rectangle.end.y - rectangle.start.y,
            width=rectangle.end.x - rectangle.start.x,
        ),
                   schema_id=schema_id,
                   title=title,
                   classifications=classifications,
                   **extra)


class LBV1Polygon(LBV1ObjectBase):
    polygon: List[PointLocation]

    def to_common(self) -> Polygon:
        return Polygon(points=[Point(x=p.x, y=p.y) for p in self.polygon])

    @classmethod
    def from_common(cls, polygon: Polygon,
                    classifications: List[ClassificationAnnotation],
                    schema_id: str, title: str, extra) -> "LBV1Polygon":
        return cls(polygon=[
            PointLocation(x=point.x, y=point.y) for point in polygon.points
        ],
                   classifications=classifications,
                   schema_id=schema_id,
                   title=title,
                   **extra)


class LBV1Point(LBV1ObjectBase):
    point: PointLocation

    def to_common(self) -> Point:
        return Point(x=self.point.x, y=self.point.y)

    @classmethod
    def from_common(cls, point: Point,
                    classifications: List[ClassificationAnnotation],
                    schema_id: str, title: str, extra) -> "LBV1Point":
        return cls(point=PointLocation(x=point.x, y=point.y),
                   classifications=classifications,
                   schema_id=schema_id,
                   title=title,
                   **extra)


class LBV1Line(LBV1ObjectBase):
    line: List[PointLocation]

    def to_common(self):
        return Line(points=[Point(x=p.x, y=p.y) for p in self.line])

    @classmethod
    def from_common(cls, polygon: Line,
                    classifications: List[ClassificationAnnotation],
                    schema_id: str, title: str, extra) -> "LBV1Line":
        return cls(line=[
            PointLocation(x=point.x, y=point.y) for point in polygon.points
        ],
                   classifications=classifications,
                   schema_id=schema_id,
                   title=title,
                   **extra)


class LBV1Mask(LBV1ObjectBase):
    instanceURI: str

    def to_common(self):
        return Mask(mask=RasterData(url=self.instanceURI),
                    color_rgb=(255, 255, 255))

    @classmethod
    def from_common(cls, mask: Mask,
                    classifications: List[ClassificationAnnotation],
                    schema_id: str, title: str, extra) -> "LBV1Mask":

        return cls(instanceURI=mask.mask.url,
                   classifications=classifications,
                   schema_id=schema_id,
                   title=title,
                   **{k: v for k, v in extra.items() if k != 'instanceURI'})


class TextPoint(BaseModel):
    start: int
    end: int


class Location(BaseModel):
    location: TextPoint


class LBV1TextEntity(LBV1ObjectBase):
    data: Location
    format: str = "text.location"
    version: int = 1

    def to_common(self):
        return TextEntity(
            start=self.data.location.start,
            end=self.data.location.end,
        )

    @classmethod
    def from_common(cls, text_entity: TextEntity,
                    classifications: List[ClassificationAnnotation],
                    schema_id: str, title: str, extra) -> "LBV1TextEntity":

        return cls(data={
            'location': {
                'start': text_entity.start,
                'end': text_entity.end
            }
        },
                   classifications=classifications,
                   schema_id=schema_id,
                   title=title,
                   **extra)


class LBV1Objects(BaseModel):
    objects: List[Union[LBV1Line, LBV1Point, LBV1Polygon, LBV1Rectangle,
                        LBV1TextEntity, LBV1Mask]]

    def to_common(self):
        objects = [
            ObjectAnnotation(value=obj.to_common(),
                             classifications=[
                                 ClassificationAnnotation(
                                     value=cls.to_common(),
                                     schema_id=cls.schema_id,
                                     display_name=cls.title,
                                     extra={
                                         'feature_id': cls.feature_id,
                                         'title': cls.title,
                                         'value': cls.value
                                     }) for cls in obj.classifications
                             ],
                             display_name=obj.title,
                             schema_id=obj.schema_id,
                             extra={
                                 'instanceURI': obj.instanceURI,
                                 'color': obj.color,
                                 'feature_id': obj.feature_id,
                                 'value': obj.value,
                                 #'keyframe' : getattr(obj, 'keyframe', None)
                             }) for obj in self.objects
        ]
        return objects

    @classmethod
    def from_common(cls, annotations: List[AnnotationType]) -> "LBV1Objects":
        objects = []

        for annotation in annotations:
            obj = cls.lookup_object(annotation)
            if obj is not None:
                subclasses = []
                subclasses = LBV1Classifications.from_common(
                    annotation.classifications).classifications

                objects.append(
                    obj.from_common(annotation.value, subclasses,
                                    annotation.schema_id,
                                    annotation.display_name, {'keyframe' : getattr(annotation, 'keyframe' , None), ** annotation.extra}))

            else:
                raise TypeError(f"Unexpected type {type(annotation.value)}")
        return cls(objects=objects)

    @staticmethod
    def lookup_object(annotation: AnnotationType):
        return {
            Line: LBV1Line,
            Point: LBV1Point,
            Polygon: LBV1Polygon,
            Rectangle: LBV1Rectangle,
            Mask: LBV1Mask,
            TextEntity: LBV1TextEntity
        }.get(type(annotation.value))
