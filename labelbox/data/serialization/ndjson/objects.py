from typing import Any, Dict, List, Tuple, Union

from pydantic import BaseModel

from ...annotation_types.data import RasterData, TextData
from ...annotation_types.ner import TextEntity
from ...annotation_types.types import Cuid
from ...annotation_types.geometry import Rectangle, Polygon, Line, Point, Mask
from ...annotation_types.annotation import ClassificationAnnotation, ObjectAnnotation
from .classification import NDSubclassification, NDSubclassificationType
from .base import DataRow, NDAnnotation


class NDBaseObject(NDAnnotation):
    classifications: List[NDSubclassificationType] = []


class _Point(BaseModel):
    x: float
    y: float


class Bbox(BaseModel):
    top: float
    left: float
    height: float
    width: float


class NDPoint(NDBaseObject):
    point: _Point

    def to_common(self) -> Point:
        return Point(x=self.point.x, y=self.point.y)

    @classmethod
    def from_common(cls, point: Point,
                    classifications: List[ClassificationAnnotation],
                    schema_id: Cuid, extra: Dict[str, Any],
                    data: Union[RasterData, TextData]) -> "NDPoint":
        return cls(point={
            'x': point.x,
            'y': point.y
        },
                   dataRow=DataRow(id=data.uid),
                   schema_id=schema_id,
                   uuid=extra.get('uuid'),
                   classifications=classifications)


class NDLine(NDBaseObject):
    line: List[_Point]

    def to_common(self) -> Line:
        return Line(points=[Point(x=pt.x, y=pt.y) for pt in self.line])

    @classmethod
    def from_common(cls, line: Line,
                    classifications: List[ClassificationAnnotation],
                    schema_id: Cuid, extra: Dict[str, Any],
                    data: Union[RasterData, TextData]) -> "NDLine":
        return cls(line=[{
            'x': pt.x,
            'y': pt.y
        } for pt in line.points],
                   dataRow=DataRow(id=data.uid),
                   schema_id=schema_id,
                   uuid=extra.get('uuid'),
                   classifications=classifications)


class NDPolygon(NDBaseObject):
    polygon: List[_Point]

    def to_common(self) -> Polygon:
        return Polygon(points=[Point(x=pt.x, y=pt.y) for pt in self.polygon])

    @classmethod
    def from_common(cls, polygon: Polygon,
                    classifications: List[ClassificationAnnotation],
                    schema_id: Cuid, extra: Dict[str, Any],
                    data: Union[RasterData, TextData]) -> "NDPolygon":
        return cls(polygon=[{
            'x': pt.x,
            'y': pt.y
        } for pt in polygon.points],
                   dataRow=DataRow(id=data.uid),
                   schema_id=schema_id,
                   uuid=extra.get('uuid'),
                   classifications=classifications)


class NDRectangle(NDBaseObject):
    bbox: Bbox

    def to_common(self) -> Rectangle:
        return Rectangle(start=Point(x=self.bbox.left, y=self.bbox.top),
                         end=Point(x=self.bbox.left + self.bbox.width,
                                   y=self.bbox.top + self.bbox.height))

    @classmethod
    def from_common(cls, rectangle: Rectangle,
                    classifications: List[ClassificationAnnotation],
                    schema_id: Cuid, extra: Dict[str, Any],
                    data: Union[RasterData, TextData]) -> "NDRectangle":
        return cls(bbox=Bbox(top=rectangle.start.y,
                             left=rectangle.start.x,
                             height=rectangle.end.y - rectangle.start.y,
                             width=rectangle.end.x - rectangle.start.x),
                   dataRow=DataRow(id=data.uid),
                   schema_id=schema_id,
                   uuid=extra.get('uuid'),
                   classifications=classifications)


class _Mask(BaseModel):
    instanceURI: str
    colorRGB: Tuple[int, int, int]


class NDMask(NDBaseObject):
    mask: _Mask

    def to_common(self) -> Mask:
        return Mask(mask=RasterData(url=self.mask.instanceURI),
                    color=self.mask.colorRGB)

    @classmethod
    def from_common(cls, mask: Mask,
                    classifications: List[ClassificationAnnotation],
                    schema_id: Cuid, extra: Dict[str, Any],
                    data: Union[RasterData, TextData]) -> "NDMask":
        if mask.mask.url is None:
            raise ValueError(
                "Mask does not have a url. Use `LabelGenerator.add_url_to_masks`, `LabelList.add_url_to_masks`, or `Label.add_url_to_masks`."
            )
        return cls(mask=_Mask(instanceURI=mask.mask.url, colorRGB=mask.color),
                   dataRow=DataRow(id=data.uid),
                   schema_id=schema_id,
                   uuid=extra.get('uuid'),
                   classifications=classifications)


class Location(BaseModel):
    start: int
    end: int


class NDTextEntity(NDBaseObject):
    location: Location

    def to_common(self) -> TextEntity:
        return TextEntity(start=self.location.start, end=self.location.end)

    @classmethod
    def from_common(cls, text_entity: TextEntity,
                    classifications: List[ClassificationAnnotation],
                    schema_id: Cuid, extra: Dict[str, Any],
                    data: Union[RasterData, TextData]) -> "NDTextEntity":
        return cls(location=Location(
            start=text_entity.start,
            end=text_entity.end,
        ),
                   dataRow=DataRow(id=data.uid),
                   schema_id=schema_id,
                   uuid=extra.get('uuid'),
                   classifications=classifications)


class NDObject:

    @staticmethod
    def to_common(annotation: "NDObjectType") -> ObjectAnnotation:
        common_annotation = annotation.to_common()
        classifications = [
            NDSubclassification.to_common(annot)
            for annot in annotation.classifications
        ]
        return ObjectAnnotation(value=common_annotation,
                                schema_id=annotation.schema_id,
                                classifications=classifications,
                                extra={'uuid': annotation.uuid})

    @classmethod
    def from_common(
        cls, annotation: ObjectAnnotation, data: Union[RasterData, TextData]
    ) -> Union[NDLine, NDPoint, NDPolygon, NDRectangle, NDMask, NDTextEntity]:
        obj = cls.lookup_object(annotation)
        subclasses = [
            NDSubclassification.from_common(annot)
            for annot in annotation.classifications
        ]
        return obj.from_common(annotation.value, subclasses,
                               annotation.schema_id, annotation.extra, data)

    @staticmethod
    def lookup_object(annotation: ObjectAnnotation) -> "NDObjectType":
        result = {
            Line: NDLine,
            Point: NDPoint,
            Polygon: NDPolygon,
            Rectangle: NDRectangle,
            Mask: NDMask,
            TextEntity: NDTextEntity
        }.get(type(annotation.value))
        if result is None:
            raise TypeError(
                f"Unable to convert object to MAL format. `{type(annotation.value)}`"
            )
        return result


NDObjectType = Union[NDLine, NDPolygon, NDPoint, NDRectangle, NDMask,
                     NDTextEntity]
