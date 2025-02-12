from collections import defaultdict
import copy
from itertools import groupby
from operator import itemgetter
from typing import Generator, List, Tuple, Union
from uuid import uuid4

from pydantic import BaseModel

from ...annotation_types.annotation import (
    ClassificationAnnotation,
    ObjectAnnotation,
)
from ...annotation_types.collection import LabelCollection
from ...annotation_types.label import Label
from ...annotation_types.llm_prompt_response.prompt import (
    PromptClassificationAnnotation,
)
from ...annotation_types.metrics import ConfusionMatrixMetric, ScalarMetric
from ...annotation_types.mmc import MessageEvaluationTaskAnnotation
from ...annotation_types.relationship import RelationshipAnnotation
from ...annotation_types.video import (
    VideoClassificationAnnotation,
    VideoMaskAnnotation,
    VideoObjectAnnotation,
)
from labelbox.types import DocumentRectangle, DocumentEntity
from .classification import (
    NDChecklistSubclass,
    NDClassification,
    NDClassificationType,
    NDPromptClassification,
    NDPromptClassificationType,
    NDPromptText,
    NDRadioSubclass,
)
from .metric import NDConfusionMatrixMetric, NDMetricAnnotation, NDScalarMetric
from .mmc import NDMessageTask
from .objects import (
    NDObject,
    NDObjectType,
    NDSegments,
    NDVideoMasks,
)
from .relationship import NDRelationship

AnnotationType = Union[
    NDObjectType,
    NDClassificationType,
    NDPromptClassificationType,
    NDConfusionMatrixMetric,
    NDScalarMetric,
    NDSegments,
    NDVideoMasks,
    NDRelationship,
    NDPromptText,
    NDMessageTask,
]


class NDLabel(BaseModel):
    annotations: AnnotationType

    @classmethod
    def from_common(
        cls, data: LabelCollection
    ) -> Generator["NDLabel", None, None]:
        for label in data:
            yield from cls._create_relationship_annotations(label)
            yield from cls._create_non_video_annotations(label)
            yield from cls._create_video_annotations(label)

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
                    RelationshipAnnotation,
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
            elif isinstance(annotation, PromptClassificationAnnotation):
                yield NDPromptClassification.from_common(annotation, label.data)
            elif isinstance(annotation, MessageEvaluationTaskAnnotation):
                yield NDMessageTask.from_common(annotation, label.data)
            else:
                raise TypeError(
                    f"Unable to convert object to MAL format. `{type(getattr(annotation, 'value',annotation))}`"
                )

    @classmethod
    def _create_relationship_annotations(
        cls, label: Label
    ) -> Generator[NDRelationship, None, None]:
        """Processes relationship annotations from a label, converting them to NDJSON format.

        Args:
            label: Label containing relationship annotations to be processed

        Yields:
            NDRelationship: Validated relationship annotations in NDJSON format

        Raises:
            TypeError: If source/target types are invalid:
                - Source:
                    - For PDF target annotations (DocumentRectangle, DocumentEntity): source must be ObjectAnnotation or ClassificationAnnotation
                    - For other target annotations: source must be ObjectAnnotation
                - Target:
                    - Target must always be ObjectAnnotation
            ValueError: If relationship validation fails:
                - For PDF target annotations: either source or source_ontology_name must be provided
        """
        for annotation in label.annotations:
            if isinstance(annotation, RelationshipAnnotation):
                uuid1 = uuid4()
                uuid2 = uuid4()
                source = copy.copy(annotation.value.source)
                target = copy.copy(annotation.value.target)

                # Check if source type is valid based on target type
                if isinstance(
                    target.value, (DocumentRectangle, DocumentEntity)
                ):
                    if source is not None and not isinstance(
                        source, (ObjectAnnotation, ClassificationAnnotation)
                    ):
                        raise TypeError(
                            f"Unable to create relationship with invalid source. For PDF targets, "
                            f"source must be ObjectAnnotation or ClassificationAnnotation. Got: {type(source)}"
                        )
                    if (
                        source is None
                        and annotation.value.source_ontology_name is None
                    ):
                        raise ValueError(
                            "Unable to create relationship - either source or source_ontology_name must be provided"
                        )
                elif not isinstance(source, ObjectAnnotation):
                    raise TypeError(
                        f"Unable to create relationship with non ObjectAnnotation source: {type(source)}"
                    )

                # Check if target type is valid
                if not isinstance(target, ObjectAnnotation):
                    raise TypeError(
                        f"Unable to create relationship with non ObjectAnnotation target: {type(target)}"
                    )

                if source is not None and not source._uuid:
                    source._uuid = uuid1
                if not target._uuid:
                    target._uuid = uuid2
                yield NDRelationship.from_common(annotation, label.data)
