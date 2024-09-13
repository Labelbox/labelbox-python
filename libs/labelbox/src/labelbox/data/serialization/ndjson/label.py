from itertools import groupby
from operator import itemgetter
from typing import Dict, Generator, List, Tuple, Union
from collections import defaultdict

from ...annotation_types.annotation import (
    ClassificationAnnotation,
    ObjectAnnotation,
)
from ...annotation_types.relationship import RelationshipAnnotation
from ...annotation_types.video import (
    DICOMObjectAnnotation,
    VideoClassificationAnnotation,
)
from ...annotation_types.video import VideoObjectAnnotation, VideoMaskAnnotation
from ...annotation_types.collection import LabelCollection, LabelGenerator
from ...annotation_types.data import DicomData, ImageData, TextData, VideoData
from ...annotation_types.data.generic_data_row_data import GenericDataRowData
from ...annotation_types.label import Label
from ...annotation_types.ner import TextEntity, ConversationEntity
from ...annotation_types.metrics import ScalarMetric, ConfusionMatrixMetric
from ...annotation_types.llm_prompt_response.prompt import (
    PromptClassificationAnnotation,
)
from ...annotation_types.mmc import MessageEvaluationTaskAnnotation

from .metric import NDScalarMetric, NDMetricAnnotation, NDConfusionMatrixMetric
from .classification import (
    NDChecklistSubclass,
    NDClassification,
    NDClassificationType,
    NDRadioSubclass,
    NDPromptClassification,
    NDPromptClassificationType,
    NDPromptText,
)
from .objects import (
    NDObject,
    NDObjectType,
    NDSegments,
    NDDicomSegments,
    NDVideoMasks,
    NDDicomMasks,
)
from .mmc import NDMessageTask
from .relationship import NDRelationship
from .base import DataRow
from pydantic import BaseModel, ValidationError
from .base import subclass_registry, _SubclassRegistryBase
from pydantic_core import PydanticUndefined
from contextlib import suppress

AnnotationType = Union[
    NDObjectType,
    NDClassificationType,
    NDPromptClassificationType,
    NDConfusionMatrixMetric,
    NDScalarMetric,
    NDDicomSegments,
    NDSegments,
    NDDicomMasks,
    NDVideoMasks,
    NDRelationship,
    NDPromptText,
    NDMessageTask,
]


class NDLabel(BaseModel):
    annotations: List[_SubclassRegistryBase]

    def __init__(self, **kwargs):
        # NOTE: Deserialization of subclasses in pydantic is difficult, see here https://blog.devgenius.io/deserialize-child-classes-with-pydantic-that-gonna-work-784230e1cf83
        # Below implements the subclass registry as mentioned in the article. The python dicts we pass in can be missing certain fields
        # we essentially have to infer the type against all sub classes that have the _SubclasssRegistryBase inheritance.
        # It works by checking if the keys of our annotations we are missing in matches any required subclass.
        # More keys are prioritized over less keys (closer match). This is used when importing json to our base models not a lot of customer workflows
        # depend on this method but this works for all our existing tests with the bonus of added validation. (no subclass found it throws an error)

        for index, annotation in enumerate(kwargs["annotations"]):
            if isinstance(annotation, dict):
                item_annotation_keys = annotation.keys()
                key_subclass_combos = defaultdict(list)
                for subclass in subclass_registry.values():
                    # Get all required keys from subclass
                    annotation_keys = []
                    for k, field in subclass.model_fields.items():
                        if field.default == PydanticUndefined and k != "uuid":
                            if (
                                hasattr(field, "alias")
                                and field.alias in item_annotation_keys
                            ):
                                annotation_keys.append(field.alias)
                            elif (
                                hasattr(field, "validation_alias")
                                and field.validation_alias
                                in item_annotation_keys
                            ):
                                annotation_keys.append(field.validation_alias)
                            else:
                                annotation_keys.append(k)

                    key_subclass_combos[subclass].extend(annotation_keys)

                # Sort by subclass that has the most keys i.e. the one with the most keys that matches is most likely our subclass
                key_subclass_combos = dict(
                    sorted(
                        key_subclass_combos.items(),
                        key=lambda x: len(x[1]),
                        reverse=True,
                    )
                )

                for subclass, key_subclass_combo in key_subclass_combos.items():
                    # Choose the keys from our dict we supplied that matches the required keys of a subclass
                    check_required_keys = all(
                        key in list(item_annotation_keys)
                        for key in key_subclass_combo
                    )
                    if check_required_keys:
                        # Keep trying subclasses until we find one that has valid values (does not throw an validation error)
                        with suppress(ValidationError):
                            annotation = subclass(**annotation)
                            break
                if isinstance(annotation, dict):
                    raise ValueError(
                        f"Could not find subclass for fields: {item_annotation_keys}"
                    )

            kwargs["annotations"][index] = annotation
        super().__init__(**kwargs)

    class _Relationship(BaseModel):
        """This object holds information about the relationship"""

        ndjson: NDRelationship
        source: str
        target: str

    class _AnnotationGroup(BaseModel):
        """Stores all the annotations and relationships per datarow"""

        data_row: DataRow = None
        ndjson_annotations: Dict[str, AnnotationType] = {}
        relationships: List["NDLabel._Relationship"] = []

    def to_common(self) -> LabelGenerator:
        annotation_groups = defaultdict(NDLabel._AnnotationGroup)

        for ndjson_annotation in self.annotations:
            key = (
                ndjson_annotation.data_row.id
                or ndjson_annotation.data_row.global_key
            )
            group = annotation_groups[key]

            if isinstance(ndjson_annotation, NDRelationship):
                group.relationships.append(
                    NDLabel._Relationship(
                        ndjson=ndjson_annotation,
                        source=ndjson_annotation.relationship.source,
                        target=ndjson_annotation.relationship.target,
                    )
                )
            else:
                # if this is the first object in this group, we
                # take note of the DataRow this group belongs to
                # and store it in the _AnnotationGroupTuple
                if not group.ndjson_annotations:
                    group.data_row = ndjson_annotation.data_row

                # if this assertion fails and it's a valid case,
                # we need to change the value type of
                # `_AnnotationGroupTuple.ndjson_objects` to accept a list of objects
                # and adapt the code to support duplicate UUIDs
                assert (
                    ndjson_annotation.uuid not in group.ndjson_annotations
                ), f"UUID '{ndjson_annotation.uuid}' is not unique"

                group.ndjson_annotations[ndjson_annotation.uuid] = (
                    ndjson_annotation
                )

        return LabelGenerator(
            data=self._generate_annotations(annotation_groups)
        )

    @classmethod
    def from_common(
        cls, data: LabelCollection
    ) -> Generator["NDLabel", None, None]:
        for label in data:
            yield from cls._create_non_video_annotations(label)
            yield from cls._create_video_annotations(label)

    def _generate_annotations(
        self, annotation_groups: Dict[str, _AnnotationGroup]
    ) -> Generator[Label, None, None]:
        for _, group in annotation_groups.items():
            relationship_annotations: Dict[str, ObjectAnnotation] = {}
            annotations = []
            # first, we iterate through all the NDJSON objects and store the
            # deserialized objects in the _AnnotationGroupTuple
            # object *if* the object can be used in a relationship
            for uuid, ndjson_annotation in group.ndjson_annotations.items():
                if isinstance(ndjson_annotation, NDDicomSegments):
                    annotations.extend(
                        NDDicomSegments.to_common(
                            ndjson_annotation,
                            ndjson_annotation.name,
                            ndjson_annotation.schema_id,
                        )
                    )
                elif isinstance(ndjson_annotation, NDSegments):
                    annotations.extend(
                        NDSegments.to_common(
                            ndjson_annotation,
                            ndjson_annotation.name,
                            ndjson_annotation.schema_id,
                        )
                    )
                elif isinstance(ndjson_annotation, NDDicomMasks):
                    annotations.append(
                        NDDicomMasks.to_common(ndjson_annotation)
                    )
                elif isinstance(ndjson_annotation, NDVideoMasks):
                    annotations.append(
                        NDVideoMasks.to_common(ndjson_annotation)
                    )
                elif isinstance(ndjson_annotation, NDObjectType.__args__):
                    annotation = NDObject.to_common(ndjson_annotation)
                    annotations.append(annotation)
                    relationship_annotations[uuid] = annotation
                elif isinstance(
                    ndjson_annotation, NDClassificationType.__args__
                ):
                    annotations.extend(
                        NDClassification.to_common(ndjson_annotation)
                    )
                elif isinstance(
                    ndjson_annotation, (NDScalarMetric, NDConfusionMatrixMetric)
                ):
                    annotations.append(
                        NDMetricAnnotation.to_common(ndjson_annotation)
                    )
                elif isinstance(ndjson_annotation, NDPromptClassificationType):
                    annotation = NDPromptClassification.to_common(
                        ndjson_annotation
                    )
                    annotations.append(annotation)
                elif isinstance(ndjson_annotation, NDMessageTask):
                    annotations.append(ndjson_annotation.to_common())
                else:
                    raise TypeError(
                        f"Unsupported annotation. {type(ndjson_annotation)}"
                    )

            # after all the annotations have been discovered, we can now create
            # the relationship objects and use references to the objects
            # involved
            for relationship in group.relationships:
                try:
                    source, target = (
                        relationship_annotations[relationship.source],
                        relationship_annotations[relationship.target],
                    )
                except KeyError:
                    raise ValueError(
                        f"Relationship object refers to nonexistent object with UUID '{relationship.source}' and/or '{relationship.target}'"
                    )
                annotations.append(
                    NDRelationship.to_common(
                        relationship.ndjson, source, target
                    )
                )

            yield Label(
                annotations=annotations,
                data=self._infer_media_type(group.data_row, annotations),
            )

    def _infer_media_type(
        self,
        data_row: DataRow,
        annotations: List[
            Union[
                TextEntity,
                ConversationEntity,
                VideoClassificationAnnotation,
                DICOMObjectAnnotation,
                VideoObjectAnnotation,
                ObjectAnnotation,
                ClassificationAnnotation,
                ScalarMetric,
                ConfusionMatrixMetric,
            ]
        ],
    ) -> Union[TextData, VideoData, ImageData]:
        if len(annotations) == 0:
            raise ValueError("Missing annotations while inferring media type")

        types = {type(annotation) for annotation in annotations}
        data = GenericDataRowData
        if (TextEntity in types) or (ConversationEntity in types):
            data = TextData
        elif (
            VideoClassificationAnnotation in types
            or VideoObjectAnnotation in types
        ):
            data = VideoData
        elif DICOMObjectAnnotation in types:
            data = DicomData

        if data_row.id:
            return data(uid=data_row.id)
        else:
            return data(global_key=data_row.global_key)

    @staticmethod
    def _get_consecutive_frames(
        frames_indices: List[int],
    ) -> List[Tuple[int, int]]:
        consecutive = []
        for k, g in groupby(enumerate(frames_indices), lambda x: x[0] - x[1]):
            group = list(map(itemgetter(1), g))
            consecutive.append((group[0], group[-1]))
        return consecutive

    @classmethod
    def _get_segment_frame_ranges(
        cls,
        annotation_group: List[
            Union[VideoClassificationAnnotation, VideoObjectAnnotation]
        ],
    ) -> List[Tuple[int, int]]:
        sorted_frame_segment_indices = sorted(
            [
                (annotation.frame, annotation.segment_index)
                for annotation in annotation_group
                if annotation.segment_index is not None
            ]
        )
        if len(sorted_frame_segment_indices) == 0:
            # Group segment by consecutive frames, since `segment_index` is not present
            return cls._get_consecutive_frames(
                sorted([annotation.frame for annotation in annotation_group])
            )
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
                f"Video annotations cannot partially have `segment_index` set"
            )

    @classmethod
    def _create_video_annotations(
        cls, label: Label
    ) -> Generator[Union[NDChecklistSubclass, NDRadioSubclass], None, None]:
        video_annotations = defaultdict(list)
        for annot in label.annotations:
            if isinstance(
                annot, (VideoClassificationAnnotation, VideoObjectAnnotation)
            ):
                video_annotations[annot.feature_schema_id or annot.name].append(
                    annot
                )
            elif isinstance(annot, VideoMaskAnnotation):
                yield NDObject.from_common(annotation=annot, data=label.data)

        for annotation_group in video_annotations.values():
            segment_frame_ranges = cls._get_segment_frame_ranges(
                annotation_group
            )
            if isinstance(annotation_group[0], VideoClassificationAnnotation):
                annotation = annotation_group[0]
                frames_data = []
                for frames in segment_frame_ranges:
                    frames_data.append({"start": frames[0], "end": frames[-1]})
                annotation.extra.update({"frames": frames_data})
                yield NDClassification.from_common(annotation, label.data)

            elif isinstance(annotation_group[0], VideoObjectAnnotation):
                segments = []
                for start_frame, end_frame in segment_frame_ranges:
                    segment = []
                    for annotation in annotation_group:
                        if (
                            annotation.keyframe
                            and start_frame <= annotation.frame <= end_frame
                        ):
                            segment.append(annotation)
                    segments.append(segment)
                yield NDObject.from_common(segments, label.data)

    @classmethod
    def _create_non_video_annotations(cls, label: Label):
        non_video_annotations = [
            annot
            for annot in label.annotations
            if not isinstance(
                annot,
                (
                    VideoClassificationAnnotation,
                    VideoObjectAnnotation,
                    VideoMaskAnnotation,
                ),
            )
        ]
        for annotation in non_video_annotations:
            if isinstance(annotation, ClassificationAnnotation):
                yield NDClassification.from_common(annotation, label.data)
            elif isinstance(annotation, ObjectAnnotation):
                yield NDObject.from_common(annotation, label.data)
            elif isinstance(annotation, (ScalarMetric, ConfusionMatrixMetric)):
                yield NDMetricAnnotation.from_common(annotation, label.data)
            elif isinstance(annotation, RelationshipAnnotation):
                yield NDRelationship.from_common(annotation, label.data)
            elif isinstance(annotation, PromptClassificationAnnotation):
                yield NDPromptClassification.from_common(annotation, label.data)
            elif isinstance(annotation, MessageEvaluationTaskAnnotation):
                yield NDMessageTask.from_common(annotation, label.data)
            else:
                raise TypeError(
                    f"Unable to convert object to MAL format. `{type(getattr(annotation, 'value',annotation))}`"
                )
