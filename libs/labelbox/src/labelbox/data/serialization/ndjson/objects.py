from io import BytesIO
from typing import Any, Dict, List, Tuple, Union, Optional
import base64

from labelbox.data.annotation_types.ner.conversation_entity import ConversationEntity
from labelbox.data.annotation_types.video import VideoObjectAnnotation, DICOMObjectAnnotation
from labelbox.data.mixins import ConfidenceMixin, CustomMetricsMixin, CustomMetric, CustomMetricsNotSupportedMixin
import numpy as np

from labelbox import pydantic_compat
from PIL import Image
from labelbox.data.annotation_types import feature

from labelbox.data.annotation_types.data.video import VideoData

from ...annotation_types.data import ImageData, TextData, MaskData
from ...annotation_types.ner import DocumentEntity, DocumentTextSelection, TextEntity
from ...annotation_types.types import Cuid
from ...annotation_types.geometry import DocumentRectangle, Rectangle, Polygon, Line, Point, Mask
from ...annotation_types.annotation import ClassificationAnnotation, ObjectAnnotation
from ...annotation_types.video import VideoMaskAnnotation, DICOMMaskAnnotation, MaskFrame, MaskInstance
from .classification import NDClassification, NDSubclassification, NDSubclassificationType
from .base import DataRow, NDAnnotation, NDJsonBase


class NDBaseObject(NDAnnotation):
    classifications: List[NDSubclassificationType] = []


class VideoSupported(pydantic_compat.BaseModel):
    # support for video for objects are per-frame basis
    frame: int


class DicomSupported(pydantic_compat.BaseModel):
    group_key: str


class _Point(pydantic_compat.BaseModel):
    x: float
    y: float


class Bbox(pydantic_compat.BaseModel):
    top: float
    left: float
    height: float
    width: float


class NDPoint(NDBaseObject, ConfidenceMixin, CustomMetricsMixin):
    point: _Point

    def to_common(self) -> Point:
        return Point(x=self.point.x, y=self.point.y)

    @classmethod
    def from_common(
            cls,
            uuid: str,
            point: Point,
            classifications: List[ClassificationAnnotation],
            name: str,
            feature_schema_id: Cuid,
            extra: Dict[str, Any],
            data: Union[ImageData, TextData],
            confidence: Optional[float] = None,
            custom_metrics: Optional[List[CustomMetric]] = None) -> "NDPoint":
        return cls(point={
            'x': point.x,
            'y': point.y
        },
                   data_row=DataRow(id=data.uid, global_key=data.global_key),
                   name=name,
                   schema_id=feature_schema_id,
                   uuid=uuid,
                   classifications=classifications,
                   confidence=confidence,
                   custom_metrics=custom_metrics)


class NDFramePoint(VideoSupported):
    point: _Point
    classifications: List[NDSubclassificationType] = []

    def to_common(self, name: str, feature_schema_id: Cuid,
                  segment_index: int) -> VideoObjectAnnotation:
        return VideoObjectAnnotation(frame=self.frame,
                                     segment_index=segment_index,
                                     keyframe=True,
                                     name=name,
                                     feature_schema_id=feature_schema_id,
                                     value=Point(x=self.point.x,
                                                 y=self.point.y),
                                     classifications=[
                                         NDSubclassification.to_common(annot)
                                         for annot in self.classifications
                                     ])

    @classmethod
    def from_common(
        cls,
        frame: int,
        point: Point,
        classifications: List[NDSubclassificationType],
    ):
        return cls(frame=frame,
                   point=_Point(x=point.x, y=point.y),
                   classifications=classifications)


class NDLine(NDBaseObject, ConfidenceMixin, CustomMetricsMixin):
    line: List[_Point]

    def to_common(self) -> Line:
        return Line(points=[Point(x=pt.x, y=pt.y) for pt in self.line])

    @classmethod
    def from_common(
            cls,
            uuid: str,
            line: Line,
            classifications: List[ClassificationAnnotation],
            name: str,
            feature_schema_id: Cuid,
            extra: Dict[str, Any],
            data: Union[ImageData, TextData],
            confidence: Optional[float] = None,
            custom_metrics: Optional[List[CustomMetric]] = None) -> "NDLine":
        return cls(line=[{
            'x': pt.x,
            'y': pt.y
        } for pt in line.points],
                   data_row=DataRow(id=data.uid, global_key=data.global_key),
                   name=name,
                   schema_id=feature_schema_id,
                   uuid=uuid,
                   classifications=classifications,
                   confidence=confidence,
                   custom_metrics=custom_metrics)


class NDFrameLine(VideoSupported):
    line: List[_Point]
    classifications: List[NDSubclassificationType] = []

    def to_common(self, name: str, feature_schema_id: Cuid,
                  segment_index: int) -> VideoObjectAnnotation:
        return VideoObjectAnnotation(
            frame=self.frame,
            segment_index=segment_index,
            keyframe=True,
            name=name,
            feature_schema_id=feature_schema_id,
            value=Line(points=[Point(x=pt.x, y=pt.y) for pt in self.line]),
            classifications=[
                NDSubclassification.to_common(annot)
                for annot in self.classifications
            ])

    @classmethod
    def from_common(
        cls,
        frame: int,
        line: Line,
        classifications: List[NDSubclassificationType],
    ):
        return cls(frame=frame,
                   line=[{
                       'x': pt.x,
                       'y': pt.y
                   } for pt in line.points],
                   classifications=classifications)


class NDDicomLine(NDFrameLine):

    def to_common(self, name: str, feature_schema_id: Cuid, segment_index: int,
                  group_key: str) -> DICOMObjectAnnotation:
        return DICOMObjectAnnotation(
            frame=self.frame,
            segment_index=segment_index,
            keyframe=True,
            name=name,
            feature_schema_id=feature_schema_id,
            value=Line(points=[Point(x=pt.x, y=pt.y) for pt in self.line]),
            group_key=group_key)


class NDPolygon(NDBaseObject, ConfidenceMixin, CustomMetricsMixin):
    polygon: List[_Point]

    def to_common(self) -> Polygon:
        return Polygon(points=[Point(x=pt.x, y=pt.y) for pt in self.polygon])

    @classmethod
    def from_common(
            cls,
            uuid: str,
            polygon: Polygon,
            classifications: List[ClassificationAnnotation],
            name: str,
            feature_schema_id: Cuid,
            extra: Dict[str, Any],
            data: Union[ImageData, TextData],
            confidence: Optional[float] = None,
            custom_metrics: Optional[List[CustomMetric]] = None) -> "NDPolygon":
        return cls(polygon=[{
            'x': pt.x,
            'y': pt.y
        } for pt in polygon.points],
                   data_row=DataRow(id=data.uid, global_key=data.global_key),
                   name=name,
                   schema_id=feature_schema_id,
                   uuid=uuid,
                   classifications=classifications,
                   confidence=confidence,
                   custom_metrics=custom_metrics)


class NDRectangle(NDBaseObject, ConfidenceMixin, CustomMetricsMixin):
    bbox: Bbox

    def to_common(self) -> Rectangle:
        return Rectangle(start=Point(x=self.bbox.left, y=self.bbox.top),
                         end=Point(x=self.bbox.left + self.bbox.width,
                                   y=self.bbox.top + self.bbox.height))

    @classmethod
    def from_common(
            cls,
            uuid: str,
            rectangle: Rectangle,
            classifications: List[ClassificationAnnotation],
            name: str,
            feature_schema_id: Cuid,
            extra: Dict[str, Any],
            data: Union[ImageData, TextData],
            confidence: Optional[float] = None,
            custom_metrics: Optional[List[CustomMetric]] = None
    ) -> "NDRectangle":
        return cls(bbox=Bbox(top=min(rectangle.start.y, rectangle.end.y),
                             left=min(rectangle.start.x, rectangle.end.x),
                             height=abs(rectangle.end.y - rectangle.start.y),
                             width=abs(rectangle.end.x - rectangle.start.x)),
                   data_row=DataRow(id=data.uid, global_key=data.global_key),
                   name=name,
                   schema_id=feature_schema_id,
                   uuid=uuid,
                   classifications=classifications,
                   page=extra.get('page'),
                   unit=extra.get('unit'),
                   confidence=confidence,
                   custom_metrics=custom_metrics)


class NDDocumentRectangle(NDRectangle):
    page: int
    unit: str

    def to_common(self) -> DocumentRectangle:
        return DocumentRectangle(start=Point(x=self.bbox.left, y=self.bbox.top),
                                 end=Point(x=self.bbox.left + self.bbox.width,
                                           y=self.bbox.top + self.bbox.height),
                                 page=self.page,
                                 unit=self.unit)

    @classmethod
    def from_common(
            cls,
            uuid: str,
            rectangle: DocumentRectangle,
            classifications: List[ClassificationAnnotation],
            name: str,
            feature_schema_id: Cuid,
            extra: Dict[str, Any],
            data: Union[ImageData, TextData],
            confidence: Optional[float] = None,
            custom_metrics: Optional[List[CustomMetric]] = None
    ) -> "NDRectangle":
        return cls(bbox=Bbox(top=min(rectangle.start.y, rectangle.end.y),
                             left=min(rectangle.start.x, rectangle.end.x),
                             height=abs(rectangle.end.y - rectangle.start.y),
                             width=abs(rectangle.end.x - rectangle.start.x)),
                   data_row=DataRow(id=data.uid, global_key=data.global_key),
                   name=name,
                   schema_id=feature_schema_id,
                   uuid=uuid,
                   classifications=classifications,
                   page=rectangle.page,
                   unit=rectangle.unit.value,
                   confidence=confidence,
                   custom_metrics=custom_metrics)


class NDFrameRectangle(VideoSupported):
    bbox: Bbox
    classifications: List[NDSubclassificationType] = []

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
                                      y=self.bbox.top + self.bbox.height)),
            classifications=[
                NDSubclassification.to_common(annot)
                for annot in self.classifications
            ])

    @classmethod
    def from_common(
        cls,
        frame: int,
        rectangle: Rectangle,
        classifications: List[NDSubclassificationType],
    ):
        return cls(frame=frame,
                   bbox=Bbox(top=min(rectangle.start.y, rectangle.end.y),
                             left=min(rectangle.start.x, rectangle.end.x),
                             height=abs(rectangle.end.y - rectangle.start.y),
                             width=abs(rectangle.end.x - rectangle.start.x)),
                   classifications=classifications)


class NDSegment(pydantic_compat.BaseModel):
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
        keyframe._uuid = uuid
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
            nd_frame_object_type.from_common(
                object_annotation.frame, object_annotation.value, [
                    NDSubclassification.from_common(annot)
                    for annot in object_annotation.classifications
                ])
            for object_annotation in segment
        ])


class NDDicomSegment(NDSegment):
    keyframes: List[NDDicomLine]

    @staticmethod
    def lookup_segment_object_type(segment: List) -> "NDDicomObjectType":
        """Used for determining which object type the annotation contains
        returns the object type"""
        segment_class = type(segment[0].value)
        if segment_class == Line:
            return NDDicomLine
        else:
            raise ValueError('DICOM segments only support Line objects')

    def to_common(self, name: str, feature_schema_id: Cuid, uuid: str,
                  segment_index: int, group_key: str):
        return [
            self.segment_with_uuid(
                keyframe.to_common(name=name,
                                   feature_schema_id=feature_schema_id,
                                   segment_index=segment_index,
                                   group_key=group_key), uuid)
            for keyframe in self.keyframes
        ]


class NDSegments(NDBaseObject):
    segments: List[NDSegment]

    def to_common(self, name: str, feature_schema_id: Cuid):
        result = []
        for idx, segment in enumerate(self.segments):
            result.extend(
                segment.to_common(name=name,
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
                   data_row=DataRow(id=data.uid, global_key=data.global_key),
                   name=name,
                   schema_id=feature_schema_id,
                   uuid=extra.get('uuid'))


class NDDicomSegments(NDBaseObject, DicomSupported):
    segments: List[NDDicomSegment]

    def to_common(self, name: str, feature_schema_id: Cuid):
        result = []
        for idx, segment in enumerate(self.segments):
            result.extend(
                segment.to_common(name=name,
                                  feature_schema_id=feature_schema_id,
                                  segment_index=idx,
                                  uuid=self.uuid,
                                  group_key=self.group_key))
        return result

    @classmethod
    def from_common(cls, segments: List[DICOMObjectAnnotation], data: VideoData,
                    name: str, feature_schema_id: Cuid, extra: Dict[str, Any],
                    group_key: str) -> "NDDicomSegments":

        segments = [NDDicomSegment.from_common(segment) for segment in segments]

        return cls(segments=segments,
                   dataRow=DataRow(id=data.uid, global_key=data.global_key),
                   name=name,
                   schema_id=feature_schema_id,
                   uuid=extra.get('uuid'),
                   group_key=group_key)


class _URIMask(pydantic_compat.BaseModel):
    instanceURI: str
    colorRGB: Tuple[int, int, int]


class _PNGMask(pydantic_compat.BaseModel):
    png: str


class NDMask(NDBaseObject, ConfidenceMixin, CustomMetricsMixin):
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
    def from_common(
            cls,
            uuid: str,
            mask: Mask,
            classifications: List[ClassificationAnnotation],
            name: str,
            feature_schema_id: Cuid,
            extra: Dict[str, Any],
            data: Union[ImageData, TextData],
            confidence: Optional[float] = None,
            custom_metrics: Optional[List[CustomMetric]] = None) -> "NDMask":

        if mask.mask.url is not None:
            lbv1_mask = _URIMask(instanceURI=mask.mask.url, colorRGB=mask.color)
        else:
            binary = np.all(mask.mask.value == mask.color, axis=-1)
            im_bytes = BytesIO()
            Image.fromarray(binary, 'L').save(im_bytes, format="PNG")
            lbv1_mask = _PNGMask(
                png=base64.b64encode(im_bytes.getvalue()).decode('utf-8'))

        return cls(mask=lbv1_mask,
                   data_row=DataRow(id=data.uid, global_key=data.global_key),
                   name=name,
                   schema_id=feature_schema_id,
                   uuid=uuid,
                   classifications=classifications,
                   confidence=confidence,
                   custom_metrics=custom_metrics)


class NDVideoMasksFramesInstances(pydantic_compat.BaseModel):
    frames: List[MaskFrame]
    instances: List[MaskInstance]


class NDVideoMasks(NDJsonBase, ConfidenceMixin, CustomMetricsNotSupportedMixin):
    masks: NDVideoMasksFramesInstances

    def to_common(self) -> VideoMaskAnnotation:
        for mask_frame in self.masks.frames:
            if mask_frame.im_bytes:
                mask_frame.im_bytes = base64.b64decode(
                    mask_frame.im_bytes.encode('utf-8'))

        return VideoMaskAnnotation(
            frames=self.masks.frames,
            instances=self.masks.instances,
        )

    @classmethod
    def from_common(cls, annotation, data):
        for mask_frame in annotation.frames:
            if mask_frame.im_bytes:
                mask_frame.im_bytes = base64.b64encode(
                    mask_frame.im_bytes).decode('utf-8')

        return cls(
            data_row=DataRow(id=data.uid, global_key=data.global_key),
            masks=NDVideoMasksFramesInstances(frames=annotation.frames,
                                              instances=annotation.instances),
        )


class NDDicomMasks(NDVideoMasks, DicomSupported):

    def to_common(self) -> DICOMMaskAnnotation:
        return DICOMMaskAnnotation(
            frames=self.masks.frames,
            instances=self.masks.instances,
            group_key=self.group_key,
        )

    @classmethod
    def from_common(cls, annotation, data):
        return cls(
            data_row=DataRow(id=data.uid, global_key=data.global_key),
            masks=NDVideoMasksFramesInstances(frames=annotation.frames,
                                              instances=annotation.instances),
            group_key=annotation.group_key.value,
        )


class Location(pydantic_compat.BaseModel):
    start: int
    end: int


class NDTextEntity(NDBaseObject, ConfidenceMixin, CustomMetricsMixin):
    location: Location

    def to_common(self) -> TextEntity:
        return TextEntity(start=self.location.start, end=self.location.end)

    @classmethod
    def from_common(
            cls,
            uuid: str,
            text_entity: TextEntity,
            classifications: List[ClassificationAnnotation],
            name: str,
            feature_schema_id: Cuid,
            extra: Dict[str, Any],
            data: Union[ImageData, TextData],
            confidence: Optional[float] = None,
            custom_metrics: Optional[List[CustomMetric]] = None
    ) -> "NDTextEntity":
        return cls(location=Location(
            start=text_entity.start,
            end=text_entity.end,
        ),
                   data_row=DataRow(id=data.uid, global_key=data.global_key),
                   name=name,
                   schema_id=feature_schema_id,
                   uuid=uuid,
                   classifications=classifications,
                   confidence=confidence,
                   custom_metrics=custom_metrics)


class NDDocumentEntity(NDBaseObject, ConfidenceMixin, CustomMetricsMixin):
    name: str
    text_selections: List[DocumentTextSelection]

    def to_common(self) -> DocumentEntity:
        return DocumentEntity(name=self.name,
                              text_selections=self.text_selections)

    @classmethod
    def from_common(
        cls,
        uuid: str,
        document_entity: DocumentEntity,
        classifications: List[ClassificationAnnotation],
        name: str,
        feature_schema_id: Cuid,
        extra: Dict[str, Any],
        data: Union[ImageData, TextData],
        confidence: Optional[float] = None,
        custom_metrics: Optional[List[CustomMetric]] = None
    ) -> "NDDocumentEntity":

        return cls(text_selections=document_entity.text_selections,
                   dataRow=DataRow(id=data.uid, global_key=data.global_key),
                   name=name,
                   schema_id=feature_schema_id,
                   uuid=uuid,
                   classifications=classifications,
                   confidence=confidence,
                   custom_metrics=custom_metrics)


class NDConversationEntity(NDTextEntity):
    message_id: str

    def to_common(self) -> ConversationEntity:
        return ConversationEntity(start=self.location.start,
                                  end=self.location.end,
                                  message_id=self.message_id)

    @classmethod
    def from_common(
        cls,
        uuid: str,
        conversation_entity: ConversationEntity,
        classifications: List[ClassificationAnnotation],
        name: str,
        feature_schema_id: Cuid,
        extra: Dict[str, Any],
        data: Union[ImageData, TextData],
        confidence: Optional[float] = None,
        custom_metrics: Optional[List[CustomMetric]] = None
    ) -> "NDConversationEntity":
        return cls(location=Location(start=conversation_entity.start,
                                     end=conversation_entity.end),
                   message_id=conversation_entity.message_id,
                   dataRow=DataRow(id=data.uid, global_key=data.global_key),
                   name=name,
                   schema_id=feature_schema_id,
                   uuid=uuid,
                   classifications=classifications,
                   confidence=confidence,
                   custom_metrics=custom_metrics)


class NDObject:

    @staticmethod
    def to_common(annotation: "NDObjectType") -> ObjectAnnotation:
        common_annotation = annotation.to_common()
        classifications = [
            NDSubclassification.to_common(annot)
            for annot in annotation.classifications
        ]
        confidence = annotation.confidence if hasattr(annotation,
                                                      'confidence') else None

        custom_metrics = annotation.custom_metrics if hasattr(
            annotation, 'custom_metrics') else None
        return ObjectAnnotation(value=common_annotation,
                                name=annotation.name,
                                feature_schema_id=annotation.schema_id,
                                classifications=classifications,
                                extra={
                                    'uuid': annotation.uuid,
                                    'page': annotation.page,
                                    'unit': annotation.unit
                                },
                                confidence=confidence,
                                custom_metrics=custom_metrics)

    @classmethod
    def from_common(
        cls,
        annotation: Union[ObjectAnnotation, List[List[VideoObjectAnnotation]],
                          VideoMaskAnnotation], data: Union[ImageData, TextData]
    ) -> Union[NDLine, NDPoint, NDPolygon, NDDocumentRectangle, NDRectangle,
               NDMask, NDTextEntity]:
        obj = cls.lookup_object(annotation)

        # if it is video segments
        if (obj == NDSegments or obj == NDDicomSegments):

            first_video_annotation = annotation[0][0]
            args = dict(
                segments=annotation,
                data=data,
                name=first_video_annotation.name,
                feature_schema_id=first_video_annotation.feature_schema_id,
                extra=first_video_annotation.extra)

            if isinstance(first_video_annotation, DICOMObjectAnnotation):
                group_key = first_video_annotation.group_key.value
                args.update(dict(group_key=group_key))

            return obj.from_common(**args)
        elif (obj == NDVideoMasks or obj == NDDicomMasks):
            return obj.from_common(annotation, data)

        subclasses = [
            NDSubclassification.from_common(annot)
            for annot in annotation.classifications
        ]
        optional_kwargs = {}
        if (annotation.confidence):
            optional_kwargs['confidence'] = annotation.confidence

        if (annotation.custom_metrics):
            optional_kwargs['custom_metrics'] = annotation.custom_metrics

        return obj.from_common(str(annotation._uuid), annotation.value,
                               subclasses, annotation.name,
                               annotation.feature_schema_id, annotation.extra,
                               data, **optional_kwargs)

    @staticmethod
    def lookup_object(
            annotation: Union[ObjectAnnotation, List]) -> "NDObjectType":

        if isinstance(annotation, DICOMMaskAnnotation):
            result = NDDicomMasks
        elif isinstance(annotation, VideoMaskAnnotation):
            result = NDVideoMasks
        elif isinstance(annotation, list):
            try:
                first_annotation = annotation[0][0]
            except IndexError:
                raise ValueError("Annotation list cannot be empty")

            if isinstance(first_annotation, DICOMObjectAnnotation):
                result = NDDicomSegments
            else:
                result = NDSegments
        else:
            result = {
                Line: NDLine,
                Point: NDPoint,
                Polygon: NDPolygon,
                Rectangle: NDRectangle,
                DocumentRectangle: NDDocumentRectangle,
                Mask: NDMask,
                TextEntity: NDTextEntity,
                DocumentEntity: NDDocumentEntity,
                ConversationEntity: NDConversationEntity,
            }.get(type(annotation.value))
        if result is None:
            raise TypeError(
                f"Unable to convert object to MAL format. `{type(annotation.value)}`"
            )
        return result


# NOTE: Deserialization of subclasses in pydantic is a known PIA, see here https://blog.devgenius.io/deserialize-child-classes-with-pydantic-that-gonna-work-784230e1cf83
# I could implement the registry approach suggested there, but I found that if I list subclass (that has more attributes) before the parent class, it works
# This is a bit of a hack, but it works for now
NDEntityType = Union[NDConversationEntity, NDTextEntity]
NDObjectType = Union[NDLine, NDPolygon, NDPoint, NDDocumentRectangle,
                     NDRectangle, NDMask, NDEntityType, NDDocumentEntity]

NDFrameObjectType = NDFrameRectangle, NDFramePoint, NDFrameLine
NDDicomObjectType = NDDicomLine
