from collections import defaultdict
import copy
from itertools import groupby
from operator import itemgetter
from typing import Any, Dict, Generator, List, Tuple, Union
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
from typing import List
from ...annotation_types.audio import (
    AudioClassificationAnnotation,
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
            yield from cls._create_audio_annotations(label)

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
    def _create_audio_annotations(
        cls, label: Label
    ) -> Generator[BaseModel, None, None]:
        """Create audio annotations with nested classifications (v3-like),
        while preserving v2 behavior for non-nested cases.

        Strategy:
        - Group audio annotations by classification (schema_id or name)
        - Identify root groups (not fully contained by another group's frames)
        - For each root group, build answer items grouped by value with frames
        - Recursively attach nested classifications by time containment
        """

        # 1) Collect all audio annotations grouped by classification key
        #    Use feature_schema_id when present, otherwise fall back to name
        audio_by_group: Dict[str, List[AudioClassificationAnnotation]] = defaultdict(list)
        for annot in label.annotations:
            if isinstance(annot, AudioClassificationAnnotation):
                audio_by_group[annot.feature_schema_id or annot.name].append(annot)

        if not audio_by_group:
            return

        # Helper: produce a user-facing classification name for a group
        def group_display_name(group_key: str, anns: List[AudioClassificationAnnotation]) -> str:
            # Prefer the first non-empty annotation name
            for a in anns:
                if a.name:
                    return a.name
            # Fallback to group key (may be schema id)
            return group_key

        # Helper: compute whether group A is fully contained by any other group by time
        def is_group_nested(group_key: str) -> bool:
            anns = audio_by_group[group_key]
            for ann in anns:
                # An annotation is considered nested if there exists any container in other groups
                contained = False
                for other_key, other_anns in audio_by_group.items():
                    if other_key == group_key:
                        continue
                    for parent in other_anns:
                        if parent.start_frame <= ann.start_frame and (
                            parent.end_frame is not None
                            and ann.end_frame is not None
                            and parent.end_frame >= ann.end_frame
                        ):
                            contained = True
                            break
                    if contained:
                        break
                if not contained:
                    # If any annotation in this group is not contained, group is a root
                    return False
            # All annotations were contained somewhere → nested group
            return True

        # Helper: group annotations by logical value and produce answer entries
        def group_by_value(annotations: List[AudioClassificationAnnotation]) -> List[Dict[str, Any]]:
            value_buckets: Dict[str, List[AudioClassificationAnnotation]] = defaultdict(list)

            for ann in annotations:
                # Compute grouping key depending on classification type
                if hasattr(ann.value, "answer"):
                    if isinstance(ann.value.answer, list):
                        # Checklist: stable key from selected option names
                        key = str(sorted([opt.name for opt in ann.value.answer]))
                    elif hasattr(ann.value.answer, "name"):
                        # Radio: option name
                        key = ann.value.answer.name
                    else:
                        # Text: the string value
                        key = ann.value.answer
                else:
                    key = str(ann.value)
                value_buckets[key].append(ann)

            entries: List[Dict[str, Any]] = []
            for _, anns in value_buckets.items():
                first = anns[0]
                frames = [{"start": a.start_frame, "end": a.end_frame} for a in anns]

                if hasattr(first.value, "answer") and isinstance(first.value.answer, list):
                    # Checklist: emit one entry per distinct option present in this bucket
                    # Since bucket is keyed by the combination, take names from first
                    for opt_name in sorted([o.name for o in first.value.answer]):
                        entries.append({"name": opt_name, "frames": frames})
                elif hasattr(first.value, "answer") and hasattr(first.value.answer, "name"):
                    # Radio
                    entries.append({"name": first.value.answer.name, "frames": frames})
                else:
                    # Text
                    entries.append({"value": first.value.answer, "frames": frames})

            return entries

        # Helper: check if child ann is inside any of the parent frames list
        def ann_within_frames(ann: AudioClassificationAnnotation, frames: List[Dict[str, int]]) -> bool:
            for fr in frames:
                if fr["start"] <= ann.start_frame and (
                    ann.end_frame is not None and fr["end"] is not None and fr["end"] >= ann.end_frame
                ):
                    return True
            return False

        # Helper: recursively build nested classifications for a specific parent frames list
        def build_nested_for_frames(parent_frames: List[Dict[str, int]], exclude_group: str) -> List[Dict[str, Any]]:
            nested: List[Dict[str, Any]] = []

            # Collect all annotations within parent frames across all groups except the excluded one
            all_contained: List[AudioClassificationAnnotation] = []
            for gk, ga in audio_by_group.items():
                if gk == exclude_group:
                    continue
                all_contained.extend([a for a in ga if ann_within_frames(a, parent_frames)])

            def strictly_contains(container: AudioClassificationAnnotation, inner: AudioClassificationAnnotation) -> bool:
                if container is inner:
                    return False
                if container.end_frame is None or inner.end_frame is None:
                    return False
                return container.start_frame <= inner.start_frame and container.end_frame >= inner.end_frame and (
                    container.start_frame < inner.start_frame or container.end_frame > inner.end_frame
                )

            for group_key, anns in audio_by_group.items():
                if group_key == exclude_group:
                    continue
                # Do not nest groups that are roots themselves to avoid duplicating top-level groups inside others
                if group_key in root_group_keys:
                    continue

                # Filter annotations that are contained by any parent frame
                candidate_anns = [a for a in anns if ann_within_frames(a, parent_frames)]
                if not candidate_anns:
                    continue

                # Keep only immediate children (those not strictly contained by another contained annotation)
                child_anns = []
                for a in candidate_anns:
                    has_closer_container = any(strictly_contains(b, a) for b in all_contained)
                    if not has_closer_container:
                        child_anns.append(a)
                if not child_anns:
                    continue

                # Build this child classification block
                child_entries = group_by_value(child_anns)
                # Recurse: for each answer entry, compute further nested
                for entry in child_entries:
                    entry_frames = entry.get("frames", [])
                    child_nested = build_nested_for_frames(entry_frames, group_key)
                    if child_nested:
                        entry["classifications"] = child_nested

                nested.append({
                    "name": group_display_name(group_key, anns),
                    "answer": child_entries,
                })

            return nested

        # 2) Determine root groups (not fully contained by other groups)
        root_group_keys = [k for k in audio_by_group.keys() if not is_group_nested(k)]

        # 3) Emit one NDJSON object per root classification group
        class AudioNDJSON(BaseModel):
            name: str
            answer: List[Dict[str, Any]]
            dataRow: Dict[str, str]

        for group_key in root_group_keys:
            anns = audio_by_group[group_key]
            top_entries = group_by_value(anns)

            # Attach nested to each top-level answer entry
            for entry in top_entries:
                frames = entry.get("frames", [])
                children = build_nested_for_frames(frames, group_key)
                if children:
                    entry["classifications"] = children

            yield AudioNDJSON(
                name=group_display_name(group_key, anns),
                answer=top_entries,
                dataRow={"globalKey": label.data.global_key},
            )



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
                    AudioClassificationAnnotation,
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
                    f"Unable to convert object to MAL format. `{type(getattr(annotation, 'value', annotation))}`"
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
