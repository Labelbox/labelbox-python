"""
Simplified temporal NDJSON serialization.

This module provides a streamlined approach for constructing nested hierarchical
classifications from temporal annotations (audio, video, etc.).

IMPORTANT: This module ONLY supports explicit nesting via ClassificationAnswer.classifications.
Annotations must define their hierarchy structure explicitly in the annotation objects.
Temporal containment-based inference is NOT supported.
"""

from collections import defaultdict
from typing import Any, Dict, List, Tuple
from pydantic import BaseModel

from ...annotation_types.audio import AudioClassificationAnnotation


def create_temporal_ndjson_annotations(
    annotations: List[Any], data_global_key: str, frame_extractor: callable
) -> List["TemporalNDJSON"]:
    """
    Create NDJSON temporal annotations with hierarchical structure.

    Args:
        annotations: List of temporal classification annotations
        data_global_key: Global key for the data row
        frame_extractor: Function that extracts (start, end) tuple from annotation

    Returns:
        List of TemporalNDJSON objects
    """
    if not annotations:
        return []

    # Group by classification name/schema_id
    groups = defaultdict(list)
    for ann in annotations:
        key = ann.feature_schema_id or ann.name
        groups[key].append(ann)

    results = []
    for group_key, group_anns in groups.items():
        # Get display name (prefer first non-empty name)
        display_name = next((a.name for a in group_anns if a.name), group_key)

        # Process this group recursively
        answers = _process_annotation_group(group_anns, frame_extractor)

        results.append(
            TemporalNDJSON(
                name=display_name,
                answer=answers,
                dataRow={"globalKey": data_global_key},
            )
        )

    return results


def _process_annotation_group(
    annotations: List[Any], frame_extractor: callable
) -> List[Dict[str, Any]]:
    """
    Process a group of annotations with the same name/schema_id.
    Groups by answer value and handles nested classifications recursively.
    """
    # Group by answer value
    value_groups = defaultdict(list)
    for ann in annotations:
        value_key = _get_value_key(ann)
        value_groups[value_key].append(ann)

    results = []
    for _, anns in value_groups.items():
        first = anns[0]

        # Handle different annotation types
        if hasattr(first.value, "answer"):
            answer = first.value.answer

            if isinstance(answer, list):
                # Checklist - process each option
                results.extend(_process_checklist(anns, frame_extractor))
            elif hasattr(answer, "name"):
                # Radio - merge frames and nested classifications
                results.append(_process_radio(anns, frame_extractor))
            else:
                # Text - simple value with potential nesting
                results.append(_process_text(anns, frame_extractor))
        else:
            # Fallback for unexpected structure
            results.append(_process_text(anns, frame_extractor))

    return results


def _process_checklist(
    annotations: List[Any], frame_extractor: callable
) -> List[Dict[str, Any]]:
    """Process checklist annotations - collect all unique options across all annotations."""
    # Collect all unique option names and their data
    option_data = defaultdict(lambda: {"frames": [], "nested": []})

    for ann in annotations:
        ann_start, ann_end = frame_extractor(ann)
        ann_frames = [{"start": ann_start, "end": ann_end}]

        if hasattr(ann.value, "answer") and isinstance(ann.value.answer, list):
            for opt in ann.value.answer:
                opt_name = opt.name

                # Get frames for this option (use explicit if available, else annotation frames)
                opt_frames = _extract_frames(opt, ann_frames)
                option_data[opt_name]["frames"].extend(opt_frames)

                # Collect nested classifications
                if hasattr(opt, "classifications") and opt.classifications:
                    option_data[opt_name]["nested"].extend(opt.classifications)

    # Build answer entries
    results = []
    for opt_name in sorted(option_data.keys()):
        entry = {"name": opt_name, "frames": option_data[opt_name]["frames"]}

        # Recursively process nested classifications
        if option_data[opt_name]["nested"]:
            nested = _process_nested_classifications(
                option_data[opt_name]["nested"]
            )
            if nested:
                entry["classifications"] = nested

        results.append(entry)

    return results


def _process_radio(
    annotations: List[Any], frame_extractor: callable
) -> Dict[str, Any]:
    """Process radio annotations - merge frames and nested classifications."""
    first = annotations[0]
    opt_name = first.value.answer.name

    # Collect all frames and nested classifications
    all_frames = []
    all_nested = []

    for ann in annotations:
        ann_start, ann_end = frame_extractor(ann)
        ann_frames = [{"start": ann_start, "end": ann_end}]

        # Get frames for this radio answer
        opt_frames = _extract_frames(ann.value.answer, ann_frames)
        all_frames.extend(opt_frames)

        # Collect nested
        if (
            hasattr(ann.value.answer, "classifications")
            and ann.value.answer.classifications
        ):
            all_nested.extend(ann.value.answer.classifications)

    entry = {"name": opt_name, "frames": all_frames}

    # Recursively process nested
    if all_nested:
        nested = _process_nested_classifications(all_nested)
        if nested:
            entry["classifications"] = nested

    return entry


def _process_text(
    annotations: List[Any], frame_extractor: callable
) -> Dict[str, Any]:
    """Process text annotations - collect frames and nested classifications."""
    first = annotations[0]
    text_value = (
        first.value.answer
        if hasattr(first.value, "answer")
        else str(first.value)
    )

    # Collect all frames and nested
    all_frames = []
    all_nested = []

    for ann in annotations:
        start, end = frame_extractor(ann)
        all_frames.append({"start": start, "end": end})

        # Text nesting is at annotation level
        if hasattr(ann, "classifications") and ann.classifications:
            all_nested.extend(ann.classifications)

    entry = {"value": text_value, "frames": all_frames}

    # Recursively process nested
    if all_nested:
        nested = _process_nested_classifications(all_nested)
        if nested:
            entry["classifications"] = nested

    return entry


def _process_nested_classifications(
    classifications: List[Any],
) -> List[Dict[str, Any]]:
    """
    Recursively process nested ClassificationAnnotation objects.
    This uses the same grouping logic as top-level annotations.
    """
    # Group by name/schema_id
    groups = defaultdict(list)
    for cls in classifications:
        key = cls.feature_schema_id or cls.name
        groups[key].append(cls)

    results = []
    for group_key, cls_list in groups.items():
        display_name = next((c.name for c in cls_list if c.name), group_key)

        # Group by value and process
        value_groups = defaultdict(list)
        for cls in cls_list:
            value_key = _get_value_key(cls)
            value_groups[value_key].append(cls)

        answers = []
        for _, cls_group in value_groups.items():
            first_cls = cls_group[0]

            if hasattr(first_cls.value, "answer"):
                answer = first_cls.value.answer

                if isinstance(answer, list):
                    # Checklist
                    answers.extend(_process_nested_checklist(cls_group))
                elif hasattr(answer, "name"):
                    # Radio
                    answers.append(_process_nested_radio(cls_group))
                else:
                    # Text
                    answers.append(_process_nested_text(cls_group))

        results.append({"name": display_name, "answer": answers})

    return results


def _process_nested_checklist(
    classifications: List[Any],
) -> List[Dict[str, Any]]:
    """Process nested checklist classifications."""
    option_data = defaultdict(lambda: {"frames": [], "nested": []})

    for cls in classifications:
        cls_frames = _extract_frames(cls, [])

        if hasattr(cls.value, "answer") and isinstance(cls.value.answer, list):
            for opt in cls.value.answer:
                opt_frames = _extract_frames(opt, cls_frames)
                option_data[opt.name]["frames"].extend(opt_frames)

                if hasattr(opt, "classifications") and opt.classifications:
                    option_data[opt.name]["nested"].extend(opt.classifications)

    results = []
    for opt_name in sorted(option_data.keys()):
        entry = {"name": opt_name, "frames": option_data[opt_name]["frames"]}

        if option_data[opt_name]["nested"]:
            nested = _process_nested_classifications(
                option_data[opt_name]["nested"]
            )
            if nested:
                entry["classifications"] = nested

        results.append(entry)

    return results


def _process_nested_radio(classifications: List[Any]) -> Dict[str, Any]:
    """Process nested radio classifications - merge frames."""
    first = classifications[0]
    opt_name = first.value.answer.name

    all_frames = []
    all_nested = []

    for cls in classifications:
        cls_frames = _extract_frames(cls, [])
        opt_frames = _extract_frames(cls.value.answer, cls_frames)
        all_frames.extend(opt_frames)

        if (
            hasattr(cls.value.answer, "classifications")
            and cls.value.answer.classifications
        ):
            all_nested.extend(cls.value.answer.classifications)

    entry = {"name": opt_name, "frames": all_frames}

    if all_nested:
        nested = _process_nested_classifications(all_nested)
        if nested:
            entry["classifications"] = nested

    return entry


def _process_nested_text(classifications: List[Any]) -> Dict[str, Any]:
    """Process nested text classifications."""
    first = classifications[0]
    text_value = (
        first.value.answer
        if hasattr(first.value, "answer")
        else str(first.value)
    )

    all_frames = []
    all_nested = []

    for cls in classifications:
        frames = _extract_frames(cls, [])
        all_frames.extend(frames)

        if hasattr(cls, "classifications") and cls.classifications:
            all_nested.extend(cls.classifications)

    entry = {"value": text_value, "frames": all_frames}

    if all_nested:
        nested = _process_nested_classifications(all_nested)
        if nested:
            entry["classifications"] = nested

    return entry


def _extract_frames(
    obj: Any, fallback_frames: List[Dict[str, int]]
) -> List[Dict[str, int]]:
    """
    Extract frame range from an object (annotation, answer, or classification).
    Uses explicit frames if available, otherwise falls back to provided frames.
    """
    if (
        hasattr(obj, "start_frame")
        and obj.start_frame is not None
        and hasattr(obj, "end_frame")
        and obj.end_frame is not None
    ):
        return [{"start": obj.start_frame, "end": obj.end_frame}]
    elif fallback_frames:
        return fallback_frames
    else:
        return []


def _get_value_key(obj: Any) -> str:
    """Get a stable key for grouping by answer value."""
    if hasattr(obj.value, "answer"):
        answer = obj.value.answer
        if isinstance(answer, list):
            # Checklist: stable key from selected option names
            return str(sorted([opt.name for opt in answer]))
        elif hasattr(answer, "name"):
            # Radio: option name
            return answer.name
        else:
            # Text: the string value
            return str(answer)
    else:
        return str(obj.value)


class TemporalNDJSON(BaseModel):
    """NDJSON format for temporal annotations (audio, video, etc.)."""

    name: str
    answer: List[Dict[str, Any]]
    dataRow: Dict[str, str]


# Audio-specific convenience function
def create_audio_ndjson_annotations(
    annotations: List[AudioClassificationAnnotation], data_global_key: str
) -> List[TemporalNDJSON]:
    """
    Create NDJSON audio annotations with hierarchical structure.

    Args:
        annotations: List of audio classification annotations
        data_global_key: Global key for the data row

    Returns:
        List of TemporalNDJSON objects
    """

    def audio_frame_extractor(
        ann: AudioClassificationAnnotation,
    ) -> Tuple[int, int]:
        return (ann.start_frame, ann.end_frame or ann.start_frame)

    return create_temporal_ndjson_annotations(
        annotations, data_global_key, audio_frame_extractor
    )
