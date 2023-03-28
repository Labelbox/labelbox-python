from itertools import groupby
from operator import itemgetter
from typing import Dict, Generator, List, Tuple, Union, Any
from collections import defaultdict
import warnings

from pydantic import BaseModel

from ...annotation_types.annotation import ClassificationAnnotation, ObjectAnnotation
from ...annotation_types.relationship import RelationshipAnnotation
from ...annotation_types.video import DICOMObjectAnnotation, VideoClassificationAnnotation
from ...annotation_types.video import VideoObjectAnnotation, VideoMaskAnnotation
from ...annotation_types.collection import LabelCollection, LabelGenerator
from ...annotation_types.data import DicomData, ImageData, TextData, VideoData
from ...annotation_types.label import Label
from ...annotation_types.ner import TextEntity, ConversationEntity
from ...annotation_types.classification import Dropdown
from ...annotation_types.metrics import ScalarMetric, ConfusionMatrixMetric

from .metric import NDScalarMetric, NDMetricAnnotation, NDConfusionMatrixMetric
from .classification import NDChecklistSubclass, NDClassification, NDClassificationType, NDRadioSubclass
from .objects import NDObject, NDObjectType, NDSegments, NDDicomSegments, NDVideoMasks, NDDicomMasks
from .relationship import NDRelationship
from .base import DataRow


class NDLabel(BaseModel):
    annotations: List[Union[NDObjectType, NDClassificationType,
                            NDConfusionMatrixMetric, NDScalarMetric,
                            NDDicomSegments, NDSegments, NDDicomMasks,
                            NDVideoMasks, NDRelationship]]

    class _RelationshipTuple(BaseModel):
        ndjson: NDRelationship
        source: str
        target: str

    class _AnnotationGroupTuple(BaseModel):
        data_row: DataRow = None
        ndjson_objects: Dict[str,
                             Union[NDObjectType, NDClassificationType,
                                   NDConfusionMatrixMetric, NDScalarMetric,
                                   NDDicomSegments, NDSegments, NDDicomMasks,
                                   NDVideoMasks, NDRelationship]] = {}
        relationships: List["NDLabel._RelationshipTuple"] = []
        annotations: Dict[str, ObjectAnnotation] = {}

    def to_common(self) -> LabelGenerator:
        annotation_groups = defaultdict(lambda: NDLabel._AnnotationGroupTuple())

        for ndjson in self.annotations:
            key = ndjson.data_row.id or ndjson.data_row.global_key
            group = annotation_groups[key]

            if isinstance(ndjson, NDRelationship):
                group.relationships.append(
                    NDLabel._RelationshipTuple(
                        ndjson=ndjson,
                        source=ndjson.relationship.source,
                        target=ndjson.relationship.target))
            else:
                if not group.ndjson_objects:
                    group.data_row = ndjson.data_row

                # if this assertion fails and it's a valid case,
                # we need to change the value type of
                # `_AnnotationGroupTuple.ndjson_objects` to accept a list of objects
                # and adapt the code to support duplicate UUIDs
                assert ndjson.uuid not in group.ndjson_objects, f"UUID '{ndjson.uuid}' is not unique"

                group.ndjson_objects[ndjson.uuid] = ndjson

        return LabelGenerator(
            data=self._generate_annotations(annotation_groups))

    @classmethod
    def from_common(cls,
                    data: LabelCollection) -> Generator["NDLabel", None, None]:
        for label in data:
            yield from cls._create_non_video_annotations(label)
            yield from cls._create_video_annotations(label)

    def _generate_annotations(
        self, annotation_groups: Dict[str, _AnnotationGroupTuple]
    ) -> Generator[Label, None, None]:
        for _, group in annotation_groups.items():
            annotations = []
            for uuid, ndjson in group.ndjson_objects.items():
                if isinstance(ndjson, NDDicomSegments):
                    annotations.extend(
                        NDDicomSegments.to_common(ndjson, ndjson.name,
                                                  ndjson.schema_id))
                elif isinstance(ndjson, NDSegments):
                    annotations.extend(
                        NDSegments.to_common(ndjson, ndjson.name,
                                             ndjson.schema_id))
                elif isinstance(ndjson, NDDicomMasks):
                    annotations.append(NDDicomMasks.to_common(ndjson))
                elif isinstance(ndjson, NDVideoMasks):
                    annotations.append(NDVideoMasks.to_common(ndjson))
                elif isinstance(ndjson, NDObjectType.__args__):
                    annotation = NDObject.to_common(ndjson)
                    annotations.append(annotation)
                    group.annotations[uuid] = annotation
                elif isinstance(ndjson, NDClassificationType.__args__):
                    annotations.extend(NDClassification.to_common(ndjson))
                elif isinstance(ndjson,
                                (NDScalarMetric, NDConfusionMatrixMetric)):
                    annotations.append(NDMetricAnnotation.to_common(ndjson))
                else:
                    raise TypeError(f"Unsupported annotation. {type(ndjson)}")

            for relationship in group.relationships:
                try:
                    source, target = group.annotations[
                        relationship.source], group.annotations[
                            relationship.target]
                except KeyError:
                    raise ValueError(
                        f"Relationship object refers to nonexistent object with UUID '{relationship.source}' and/or '{relationship.target}'"
                    )
                annotations.append(
                    NDRelationship.to_common(relationship.ndjson, source,
                                             target))

            yield Label(annotations=annotations,
                        data=self._infer_media_type(group.data_row,
                                                    annotations))

    def _infer_media_type(
        self, data_row: DataRow,
        annotations: List[Union[TextEntity, ConversationEntity,
                                VideoClassificationAnnotation,
                                DICOMObjectAnnotation, VideoObjectAnnotation,
                                ObjectAnnotation, ClassificationAnnotation,
                                ScalarMetric, ConfusionMatrixMetric]]
    ) -> Union[TextData, VideoData, ImageData]:
        if len(annotations) == 0:
            raise ValueError("Missing annotations while inferring media type")

        types = {type(annotation) for annotation in annotations}
        data = ImageData
        if (TextEntity in types) or (ConversationEntity in types):
            data = TextData
        elif VideoClassificationAnnotation in types or VideoObjectAnnotation in types:
            data = VideoData
        elif DICOMObjectAnnotation in types:
            data = DicomData

        if data_row.id:
            return data(uid=data_row.id)
        else:
            return data(global_key=data_row.global_key)

    @staticmethod
    def _get_consecutive_frames(
            frames_indices: List[int]) -> List[Tuple[int, int]]:
        consecutive = []
        for k, g in groupby(enumerate(frames_indices), lambda x: x[0] - x[1]):
            group = list(map(itemgetter(1), g))
            consecutive.append((group[0], group[-1]))
        return consecutive

    @classmethod
    def _get_segment_frame_ranges(
        cls, annotation_group: List[Union[VideoClassificationAnnotation,
                                          VideoObjectAnnotation]]
    ) -> List[Tuple[int, int]]:
        sorted_frame_segment_indices = sorted([
            (annotation.frame, annotation.segment_index)
            for annotation in annotation_group
            if annotation.segment_index is not None
        ])
        if len(sorted_frame_segment_indices) == 0:
            # Group segment by consecutive frames, since `segment_index` is not present
            return cls._get_consecutive_frames(
                sorted([annotation.frame for annotation in annotation_group]))
        elif len(sorted_frame_segment_indices) == len(annotation_group):
            # Group segment by segment_index
            last_segment_id = 0
            segment_groups = defaultdict(list)
            for frame, segment_index in sorted_frame_segment_indices:
                if segment_index < last_segment_id:
                    raise ValueError(
                        f"`segment_index` must be in ascending order. Please investigate video annotation at frame, '{frame}'"
                    )
                segment_groups[segment_index].append(frame)
                last_segment_id = segment_index
            frame_ranges = []
            for group in segment_groups.values():
                frame_ranges.append((group[0], group[-1]))
            return frame_ranges
        else:
            raise ValueError(
                f"Video annotations cannot partially have `segment_index` set")

    @classmethod
    def _create_video_annotations(
        cls, label: Label
    ) -> Generator[Union[NDChecklistSubclass, NDRadioSubclass], None, None]:

        video_annotations = defaultdict(list)
        for annot in label.annotations:
            if isinstance(
                    annot,
                (VideoClassificationAnnotation, VideoObjectAnnotation)):
                video_annotations[annot.feature_schema_id or
                                  annot.name].append(annot)
            elif isinstance(annot, VideoMaskAnnotation):
                yield NDObject.from_common(annotation=annot, data=label.data)

        for annotation_group in video_annotations.values():
            segment_frame_ranges = cls._get_segment_frame_ranges(
                annotation_group)
            if isinstance(annotation_group[0], VideoClassificationAnnotation):
                annotation = annotation_group[0]
                frames_data = []
                for frames in segment_frame_ranges:
                    frames_data.append({'start': frames[0], 'end': frames[-1]})
                annotation.extra.update({'frames': frames_data})
                yield NDClassification.from_common(annotation, label.data)

            elif isinstance(annotation_group[0], VideoObjectAnnotation):
                warnings.warn(
                    """Nested classifications are not currently supported
                    for video object annotations
                    and will not import alongside the object annotations.""")
                segments = []
                for start_frame, end_frame in segment_frame_ranges:
                    segment = []
                    for annotation in annotation_group:
                        if annotation.keyframe and start_frame <= annotation.frame <= end_frame:
                            segment.append(annotation)
                    segments.append(segment)
                yield NDObject.from_common(segments, label.data)

    @classmethod
    def _create_non_video_annotations(cls, label: Label):
        non_video_annotations = [
            annot for annot in label.annotations
            if not isinstance(annot, (VideoClassificationAnnotation,
                                      VideoObjectAnnotation,
                                      VideoMaskAnnotation))
        ]
        for annotation in non_video_annotations:
            if isinstance(annotation, ClassificationAnnotation):
                if isinstance(annotation.value, Dropdown):
                    raise ValueError(
                        "Dropdowns are not supported by the NDJson format."
                        " Please filter out Dropdown annotations before converting."
                    )
                yield NDClassification.from_common(annotation, label.data)
            elif isinstance(annotation, ObjectAnnotation):
                yield NDObject.from_common(annotation, label.data)
            elif isinstance(annotation, (ScalarMetric, ConfusionMatrixMetric)):
                yield NDMetricAnnotation.from_common(annotation, label.data)
            elif isinstance(annotation, RelationshipAnnotation):
                yield NDRelationship.from_common(annotation, label.data)
            else:
                raise TypeError(
                    f"Unable to convert object to MAL format. `{type(getattr(annotation, 'value',annotation))}`"
                )
