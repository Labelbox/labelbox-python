from ast import Bytes
from io import BytesIO
from typing import Any, Dict, List, Tuple, Union, Optional
import base64
import numpy as np

from pydantic import BaseModel
from PIL import Image
from labelbox.data.annotation_types import feature

from labelbox.data.annotation_types.data.video import VideoData

from ...annotation_types.data import ImageData, TextData, MaskData
from ...annotation_types.ner import TextEntity
from ...annotation_types.types import Cuid
from ...annotation_types.geometry import Rectangle, Polygon, Line, Point, Mask
from ...annotation_types.annotation import ClassificationAnnotation, ObjectAnnotation, VideoObjectAnnotation
from .classification import NDSubclassification, NDSubclassificationType
from .base import DataRow, NDAnnotation


class NDBaseObject(NDAnnotation):
    classifications: List[NDSubclassificationType] = []


class VideoSupported(BaseModel):
    #support for video for objects are per-frame basis
    frame: int


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
                    classifications: List[ClassificationAnnotation], name: str,
                    feature_schema_id: Cuid, extra: Dict[str, Any],
                    data: Union[ImageData, TextData]) -> "NDPoint":
        return cls(point={
            'x': point.x,
            'y': point.y
        },
                   dataRow=DataRow(id=data.uid),
                   name=name,
                   schema_id=feature_schema_id,
                   uuid=extra.get('uuid'),
                   classifications=classifications)


class NDFramePoint(VideoSupported):
    point: _Point

    def to_common(self, name: str, feature_schema_id: Cuid,
                  segment_index: int) -> VideoObjectAnnotation:
        return VideoObjectAnnotation(frame=self.frame,
                                     segment_index=segment_index,
                                     keyframe=True,
                                     name=name,
                                     feature_schema_id=feature_schema_id,
                                     value=Point(x=self.point.x,
                                                 y=self.point.y))

    @classmethod
    def from_common(cls, frame: int, point: Point):
        return cls(frame=frame, point=_Point(x=point.x, y=point.y))


class NDLine(NDBaseObject):
    line: List[_Point]

    def to_common(self) -> Line:
        return Line(points=[Point(x=pt.x, y=pt.y) for pt in self.line])

    @classmethod
    def from_common(cls, line: Line,
                    classifications: List[ClassificationAnnotation], name: str,
                    feature_schema_id: Cuid, extra: Dict[str, Any],
                    data: Union[ImageData, TextData]) -> "NDLine":
        return cls(line=[{
            'x': pt.x,
            'y': pt.y
        } for pt in line.points],
                   dataRow=DataRow(id=data.uid),
                   name=name,
                   schema_id=feature_schema_id,
                   uuid=extra.get('uuid'),
                   classifications=classifications)


class NDFrameLine(VideoSupported):
    line: List[_Point]

    def to_common(self, name: str, feature_schema_id: Cuid,
                  segment_index: int) -> VideoObjectAnnotation:
        return VideoObjectAnnotation(
            frame=self.frame,
            segment_index=segment_index,
            keyframe=True,
            name=name,
            feature_schema_id=feature_schema_id,
            value=Line(points=[Point(x=pt.x, y=pt.y) for pt in self.line]))

    @classmethod
    def from_common(cls, frame: int, line: Line):
        return cls(frame=frame,
                   line=[{
                       'x': pt.x,
                       'y': pt.y
                   } for pt in line.points])


class NDPolygon(NDBaseObject):
    polygon: List[_Point]

    def to_common(self) -> Polygon:
        return Polygon(points=[Point(x=pt.x, y=pt.y) for pt in self.polygon])

    @classmethod
    def from_common(cls, polygon: Polygon,
                    classifications: List[ClassificationAnnotation], name: str,
                    feature_schema_id: Cuid, extra: Dict[str, Any],
                    data: Union[ImageData, TextData]) -> "NDPolygon":
        return cls(polygon=[{
            'x': pt.x,
            'y': pt.y
        } for pt in polygon.points],
                   dataRow=DataRow(id=data.uid),
                   name=name,
                   schema_id=feature_schema_id,
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
                    classifications: List[ClassificationAnnotation], name: str,
                    feature_schema_id: Cuid, extra: Dict[str, Any],
                    data: Union[ImageData, TextData]) -> "NDRectangle":
        return cls(bbox=Bbox(top=rectangle.start.y,
                             left=rectangle.start.x,
                             height=rectangle.end.y - rectangle.start.y,
                             width=rectangle.end.x - rectangle.start.x),
                   dataRow=DataRow(id=data.uid),
                   name=name,
                   schema_id=feature_schema_id,
                   uuid=extra.get('uuid'),
                   classifications=classifications,
                   page=extra.get('page'),
                   unit=extra.get('unit'))


class NDFrameRectangle(VideoSupported):
    bbox: Bbox

    def to_common(self, name: str, feature_schema_id: Cuid,
                  segment_index: int) -> VideoObjectAnnotation:
        return VideoObjectAnnotation(
            frame=self.frame,
            segment_index=segment_index,
            keyframe=True,
            name=name,
            feature_schema_id=feature_schema_id,
            value=Rectangle(start=Point(x=self.bbox.left, y=self.bbox.top),
                            end=Point(x=self.bbox.left + self.bbox.width,
                                      y=self.bbox.top + self.bbox.height)))

    @classmethod
    def from_common(cls, frame: int, rectangle: Rectangle):
        return cls(frame=frame,
                   bbox=Bbox(top=rectangle.start.y,
                             left=rectangle.start.x,
                             height=rectangle.end.y - rectangle.start.y,
                             width=rectangle.end.x - rectangle.start.x))


class NDSegment(BaseModel):
    keyframes: List[Union[NDFrameRectangle, NDFramePoint, NDFrameLine]]

    @staticmethod
    def lookup_segment_object_type(segment: List) -> "NDFrameObjectType":
        """Used for determining which object type the annotation contains
        returns the object type"""
        result = {
            Rectangle: NDFrameRectangle,
            Point: NDFramePoint,
            Line: NDFrameLine,
        }.get(type(segment[0].value))
        return result

    @staticmethod
    def segment_with_uuid(keyframe: Union[NDFrameRectangle, NDFramePoint,
                                          NDFrameLine], uuid: str):
        keyframe.extra = {'uuid': uuid}
        return keyframe

    def to_common(self, name: str, feature_schema_id: Cuid, uuid: str,
                  segment_index: int):
        return [
            self.segment_with_uuid(
                keyframe.to_common(name=name,
                                   feature_schema_id=feature_schema_id,
                                   segment_index=segment_index), uuid)
            for keyframe in self.keyframes
        ]

    @classmethod
    def from_common(cls, segment):
        nd_frame_object_type = cls.lookup_segment_object_type(segment)

        return cls(keyframes=[
            nd_frame_object_type.from_common(object_annotation.frame,
                                             object_annotation.value)
            for object_annotation in segment
        ])


class NDSegments(NDBaseObject):
    segments: List[NDSegment]

    def to_common(self, name: str, feature_schema_id: Cuid):
        result = []
        for idx, segment in enumerate(self.segments):
            result.extend(
                NDSegment.to_common(segment,
                                    name=name,
                                    feature_schema_id=feature_schema_id,
                                    segment_index=idx,
                                    uuid=self.uuid))
        return result

    @classmethod
    def from_common(cls, segments: List[VideoObjectAnnotation], data: VideoData,
                    name: str, feature_schema_id: Cuid,
                    extra: Dict[str, Any]) -> "NDSegments":

        segments = [NDSegment.from_common(segment) for segment in segments]

        return cls(segments=segments,
                   dataRow=DataRow(id=data.uid),
                   name=name,
                   schema_id=feature_schema_id,
                   uuid=extra.get('uuid'))


class _URIMask(BaseModel):
    instanceURI: str
    colorRGB: Tuple[int, int, int]


class _PNGMask(BaseModel):
    png: str


class NDMask(NDBaseObject):
    mask: Union[_URIMask, _PNGMask]

    def to_common(self) -> Mask:
        if isinstance(self.mask, _URIMask):
            return Mask(mask=MaskData(url=self.mask.instanceURI),
                        color=self.mask.colorRGB)
        else:
            encoded_image_bytes = self.mask.png.encode('utf-8')
            image_bytes = base64.b64decode(encoded_image_bytes)
            image = np.array(Image.open(BytesIO(image_bytes)))
            if np.max(image) > 1:
                raise ValueError(
                    f"Expected binary mask. Found max value of {np.max(image)}")
            # Color is 1,1,1 because it is a binary array and we are just stacking it into 3 channels
            return Mask(mask=MaskData.from_2D_arr(image), color=(1, 1, 1))

    @classmethod
    def from_common(cls, mask: Mask,
                    classifications: List[ClassificationAnnotation], name: str,
                    feature_schema_id: Cuid, extra: Dict[str, Any],
                    data: Union[ImageData, TextData]) -> "NDMask":

        if mask.mask.url is not None:
            lbv1_mask = _URIMask(instanceURI=mask.mask.url, colorRGB=mask.color)
        else:
            binary = np.all(mask.mask.value == mask.color, axis=-1)
            im_bytes = BytesIO()
            Image.fromarray(binary, 'L').save(im_bytes, format="PNG")
            lbv1_mask = _PNGMask(
                png=base64.b64encode(im_bytes.getvalue()).decode('utf-8'))

        return cls(mask=lbv1_mask,
                   dataRow=DataRow(id=data.uid),
                   name=name,
                   schema_id=feature_schema_id,
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
                    classifications: List[ClassificationAnnotation], name: str,
                    feature_schema_id: Cuid, extra: Dict[str, Any],
                    data: Union[ImageData, TextData]) -> "NDTextEntity":
        return cls(location=Location(
            start=text_entity.start,
            end=text_entity.end,
        ),
                   dataRow=DataRow(id=data.uid),
                   name=name,
                   schema_id=feature_schema_id,
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
                                name=annotation.name,
                                feature_schema_id=annotation.schema_id,
                                classifications=classifications,
                                extra={
                                    'uuid': annotation.uuid,
                                    'page': annotation.page,
                                    'unit': annotation.unit
                                })

    @classmethod
    def from_common(
        cls, annotation: Union[ObjectAnnotation,
                               List[List[VideoObjectAnnotation]]],
        data: Union[ImageData, TextData]
    ) -> Union[NDLine, NDPoint, NDPolygon, NDRectangle, NDMask, NDTextEntity]:
        obj = cls.lookup_object(annotation)

        #if it is video segments
        if (obj == NDSegments):
            return obj.from_common(
                annotation,
                data,
                name=annotation[0][0].name,
                feature_schema_id=annotation[0][0].feature_schema_id,
                extra=annotation[0][0].extra)

        subclasses = [
            NDSubclassification.from_common(annot)
            for annot in annotation.classifications
        ]
        return obj.from_common(annotation.value, subclasses, annotation.name,
                               annotation.feature_schema_id, annotation.extra,
                               data)

    @staticmethod
    def lookup_object(
            annotation: Union[ObjectAnnotation, List]) -> "NDObjectType":
        if isinstance(annotation, list):
            result = NDSegments
        else:
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

NDFrameObjectType = NDFrameRectangle, NDFramePoint, NDFrameLine
