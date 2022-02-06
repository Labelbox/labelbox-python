from typing import Any, Dict, List, Optional, Union, Type
try:
    from typing import Literal
except:
    from typing_extensions import Literal

from pydantic import BaseModel, validator, Field
import numpy as np

from .classification import LBV1Checklist, LBV1Classifications, LBV1Radio, LBV1Text, LBV1Dropdown
from .feature import LBV1Feature
from ...annotation_types.annotation import (ClassificationAnnotation,
                                            ObjectAnnotation)
from ...annotation_types.data import MaskData
from ...annotation_types.geometry import Line, Mask, Point, Polygon, Rectangle
from ...annotation_types.ner import TextEntity
from ...annotation_types.types import Cuid


class LBV1ObjectBase(LBV1Feature):
    color: Optional[str] = None
    instanceURI: Optional[str] = None
    classifications: List[Union[LBV1Text, LBV1Radio, LBV1Dropdown,
                                LBV1Checklist]] = []

    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        res = super().dict(*args, **kwargs)
        # This means these are not video frames ..
        if self.instanceURI is None:
            res.pop('instanceURI')
        return res

    @validator('classifications', pre=True)
    def validate_subclasses(cls, value, field):
        # checklist subclasses create extra unessesary nesting. So we just remove it.
        if isinstance(value, list) and len(value):
            subclasses = []
            for v in value:
                # this is due to Checklists providing extra brackets []. We grab every item
                # in the brackets if this is the case
                if isinstance(v, list):
                    for inner_v in v:
                        subclasses.append(inner_v)
                else:
                    subclasses.append(v)
            return subclasses
        return value


class TIPointCoordinate(BaseModel):
    coordinates: List[float]


class TILineCoordinate(BaseModel):
    coordinates: List[List[float]]


class TIPolygonCoordinate(BaseModel):
    coordinates: List[List[List[float]]]


class TIRectangleCoordinate(BaseModel):
    coordinates: List[List[List[float]]]


class LBV1TIPoint(LBV1ObjectBase):
    object_type: Literal['point'] = Field(..., alias='type')
    geometry: TIPointCoordinate

    def to_common(self) -> Point:
        lng, lat = self.geometry.coordinates
        return Point(x=lng, y=lat)


class LBV1TILine(LBV1ObjectBase):
    object_type: Literal['polyline'] = Field(..., alias='type')
    geometry: TILineCoordinate

    def to_common(self) -> Line:
        return Line(points=[
            Point(x=coord[0], y=coord[1]) for coord in self.geometry.coordinates
        ])


class LBV1TIPolygon(LBV1ObjectBase):
    object_type: Literal['polygon'] = Field(..., alias='type')
    geometry: TIPolygonCoordinate

    def to_common(self) -> Polygon:
        for coord_list in self.geometry.coordinates:
            return Polygon(
                points=[Point(x=coord[0], y=coord[1]) for coord in coord_list])


class LBV1TIRectangle(LBV1ObjectBase):
    object_type: Literal['rectangle'] = Field(..., alias='type')
    geometry: TIRectangleCoordinate

    def to_common(self) -> Rectangle:
        coord_list = np.array(self.geometry.coordinates[0])

        min_x, max_x = np.min(coord_list[:, 0]), np.max(coord_list[:, 0])
        min_y, max_y = np.min(coord_list[:, 1]), np.max(coord_list[:, 1])

        start = [min_x, min_y]
        end = [max_x, max_y]

        return Rectangle(start=Point(x=start[0], y=start[1]),
                         end=Point(x=end[0], y=end[1]))


class _Point(BaseModel):
    x: float
    y: float


class _Box(BaseModel):
    top: float
    left: float
    height: float
    width: float


class LBV1Rectangle(LBV1ObjectBase):
    bbox: _Box

    def to_common(self) -> Rectangle:
        return Rectangle(start=Point(x=self.bbox.left, y=self.bbox.top),
                         end=Point(x=self.bbox.left + self.bbox.width,
                                   y=self.bbox.top + self.bbox.height))

    @classmethod
    def from_common(cls, rectangle: Rectangle,
                    classifications: List[ClassificationAnnotation],
                    feature_schema_id: Cuid, title: str,
                    extra: Dict[str, Any]) -> "LBV1Rectangle":
        return cls(bbox=_Box(
            top=rectangle.start.y,
            left=rectangle.start.x,
            height=rectangle.end.y - rectangle.start.y,
            width=rectangle.end.x - rectangle.start.x,
        ),
                   schema_id=feature_schema_id,
                   title=title,
                   classifications=classifications,
                   **extra)


class LBV1Polygon(LBV1ObjectBase):
    polygon: List[_Point]

    def to_common(self) -> Polygon:
        return Polygon(points=[Point(x=p.x, y=p.y) for p in self.polygon])

    @classmethod
    def from_common(cls, polygon: Polygon,
                    classifications: List[ClassificationAnnotation],
                    feature_schema_id: Cuid, title: str,
                    extra: Dict[str, Any]) -> "LBV1Polygon":
        return cls(
            polygon=[
                _Point(x=point.x, y=point.y) for point in polygon.points[:-1]
            ],  # drop closing point
            classifications=classifications,
            schema_id=feature_schema_id,
            title=title,
            **extra)


class LBV1Point(LBV1ObjectBase):
    point: _Point

    def to_common(self) -> Point:
        return Point(x=self.point.x, y=self.point.y)

    @classmethod
    def from_common(cls, point: Point,
                    classifications: List[ClassificationAnnotation],
                    feature_schema_id: Cuid, title: str,
                    extra: Dict[str, Any]) -> "LBV1Point":
        return cls(point=_Point(x=point.x, y=point.y),
                   classifications=classifications,
                   schema_id=feature_schema_id,
                   title=title,
                   **extra)


class LBV1Line(LBV1ObjectBase):
    line: List[_Point]

    def to_common(self) -> Line:
        return Line(points=[Point(x=p.x, y=p.y) for p in self.line])

    @classmethod
    def from_common(cls, polygon: Line,
                    classifications: List[ClassificationAnnotation],
                    feature_schema_id: Cuid, title: str,
                    extra: Dict[str, Any]) -> "LBV1Line":
        return cls(
            line=[_Point(x=point.x, y=point.y) for point in polygon.points],
            classifications=classifications,
            schema_id=feature_schema_id,
            title=title,
            **extra)


class LBV1Mask(LBV1ObjectBase):
    instanceURI: str

    def to_common(self) -> Mask:
        return Mask(mask=MaskData(url=self.instanceURI), color=(255, 255, 255))

    @classmethod
    def from_common(cls, mask: Mask,
                    classifications: List[ClassificationAnnotation],
                    feature_schema_id: Cuid, title: str,
                    extra: Dict[str, Any]) -> "LBV1Mask":
        if mask.mask.url is None:
            raise ValueError(
                "Mask does not have a url. Use `LabelGenerator.add_url_to_masks`, `LabelList.add_url_to_masks`, or `Label.add_url_to_masks`."
            )
        return cls(instanceURI=mask.mask.url,
                   classifications=classifications,
                   schema_id=feature_schema_id,
                   title=title,
                   **{k: v for k, v in extra.items() if k != 'instanceURI'})


class _TextPoint(BaseModel):
    start: int
    end: int


class _Location(BaseModel):
    location: _TextPoint


class LBV1TextEntity(LBV1ObjectBase):
    data: _Location
    format: str = "text.location"
    version: int = 1

    def to_common(self) -> TextEntity:
        return TextEntity(
            start=self.data.location.start,
            end=self.data.location.end,
        )

    @classmethod
    def from_common(cls, text_entity: TextEntity,
                    classifications: List[ClassificationAnnotation],
                    feature_schema_id: Cuid, title: str,
                    extra: Dict[str, Any]) -> "LBV1TextEntity":
        return cls(data=_Location(
            location=_TextPoint(start=text_entity.start, end=text_entity.end)),
                   classifications=classifications,
                   schema_id=feature_schema_id,
                   title=title,
                   **extra)


class LBV1Objects(BaseModel):
    objects: List[Union[LBV1Line, LBV1Point, LBV1Polygon, LBV1Rectangle,
                        LBV1TextEntity, LBV1Mask, LBV1TIPoint, LBV1TILine,
                        LBV1TIPolygon, LBV1TIRectangle]]

    def to_common(self) -> List[ObjectAnnotation]:
        objects = [
            ObjectAnnotation(value=obj.to_common(),
                             classifications=[
                                 ClassificationAnnotation(
                                     value=cls.to_common(),
                                     feature_schema_id=cls.schema_id,
                                     name=cls.title,
                                     extra={
                                         'feature_id': cls.feature_id,
                                         'title': cls.title,
                                         'value': cls.value
                                     }) for cls in obj.classifications
                             ],
                             name=obj.title,
                             feature_schema_id=obj.schema_id,
                             extra={
                                 'instanceURI': obj.instanceURI,
                                 'color': obj.color,
                                 'feature_id': obj.feature_id,
                                 'value': obj.value,
                             }) for obj in self.objects
        ]
        return objects

    @classmethod
    def from_common(cls, annotations: List[ObjectAnnotation]) -> "LBV1Objects":
        objects = []
        for annotation in annotations:
            obj = cls.lookup_object(annotation)
            subclasses = LBV1Classifications.from_common(
                annotation.classifications).classifications

            objects.append(
                obj.from_common(
                    annotation.value, subclasses, annotation.feature_schema_id,
                    annotation.name, {
                        'keyframe': getattr(annotation, 'keyframe', None),
                        **annotation.extra
                    }))
        return cls(objects=objects)

    @staticmethod
    def lookup_object(
        annotation: ObjectAnnotation
    ) -> Type[Union[LBV1Line, LBV1Point, LBV1Polygon, LBV1Rectangle, LBV1Mask,
                    LBV1TextEntity]]:
        result = {
            Line: LBV1Line,
            Point: LBV1Point,
            Polygon: LBV1Polygon,
            Rectangle: LBV1Rectangle,
            Mask: LBV1Mask,
            TextEntity: LBV1TextEntity
        }.get(type(annotation.value))
        if result is None:
            raise TypeError(f"Unexpected type {type(annotation.value)}")
        return result
