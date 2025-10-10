"""
Temporal NDJSON serialization for new temporal classification structure.

Handles TemporalClassificationText, TemporalClassificationQuestion, and TemporalClassificationAnswer
with frame validation and recursive nesting support.
"""

import logging
from collections import defaultdict
from typing import Any, Dict, List, Tuple, Union
from pydantic import BaseModel

from ...annotation_types.temporal import (
    TemporalClassificationText,
    TemporalClassificationQuestion,
)

logger = logging.getLogger(__name__)


class TemporalNDJSON(BaseModel):
    """NDJSON structure for temporal annotations"""

    name: str
    answer: List[Dict[str, Any]]
    dataRow: Dict[str, str]


def create_temporal_ndjson_classifications(
    annotations: List[
        Union[TemporalClassificationText, TemporalClassificationQuestion]
    ],
    data_global_key: str,
) -> List[TemporalNDJSON]:
    """
    Create NDJSON temporal annotations from new temporal classification types.

    Args:
        annotations: List of TemporalClassificationText or TemporalClassificationQuestion
        data_global_key: Global key for the data row

    Returns:
        List of TemporalNDJSON objects ready for serialization
    """
    if not annotations:
        return []

    # Group by classification name
    groups = defaultdict(list)
    for ann in annotations:
        groups[ann.name].append(ann)

    results = []
    for group_key, group_anns in groups.items():
        # Get display name (prefer first non-empty name)
        display_name = next((a.name for a in group_anns if a.name), group_key)

        # Process based on annotation type
        first_ann = group_anns[0]

        if isinstance(first_ann, TemporalClassificationText):
            answers = _process_text_group(group_anns, parent_frames=None)
        elif isinstance(first_ann, TemporalClassificationQuestion):
            answers = _process_question_group(group_anns, parent_frames=None)
        else:
            logger.warning(
                f"Unknown temporal annotation type: {type(first_ann)}"
            )
            continue

        if answers:  # Only add if we have valid answers
            results.append(
                TemporalNDJSON(
                    name=display_name,
                    answer=answers,
                    dataRow={"globalKey": data_global_key},
                )
            )

    return results


def _process_text_group(
    annotations: List[TemporalClassificationText],
    parent_frames: List[Tuple[int, int]] = None,
) -> List[Dict[str, Any]]:
    """
    Process TemporalClassificationText annotations.

    Each annotation can have multiple (start, end, text) tuples.
    Groups by text value and merges frames.

    Nested classifications are assigned to text values based on frame overlap.
    """
    # Collect all text values with their frames
    text_data = defaultdict(lambda: {"frames": []})

    # Collect all nested classifications from all annotations
    all_nested_classifications = []

    for ann in annotations:
        for start, end, text_value in ann.value:
            # Validate frames against parent if provided
            if parent_frames and not _is_frame_subset(
                [(start, end)], parent_frames
            ):
                logger.warning(
                    f"Text value frames ({start}, {end}) not subset of parent frames {parent_frames}. Discarding."
                )
                continue

            text_data[text_value]["frames"].append({"start": start, "end": end})

        # Collect nested classifications at annotation level (not per text value)
        if ann.classifications:
            all_nested_classifications.extend(ann.classifications)

    # Track which nested classifications were assigned
    assigned_nested = set()

    # Build results
    results = []
    for text_value, data in text_data.items():
        # Deduplicate frames
        unique_frames = _deduplicate_frames(data["frames"])

        entry = {
            "value": text_value,
            "frames": unique_frames,
        }

        # Assign nested classifications based on frame overlap
        if all_nested_classifications:
            parent_frame_tuples = [
                (f["start"], f["end"]) for f in unique_frames
            ]
            # Filter nested classifications that overlap with this text value's frames
            relevant_nested = _filter_classifications_by_overlap(
                all_nested_classifications, parent_frame_tuples
            )
            if relevant_nested:
                # Track that these were assigned
                for cls in relevant_nested:
                    assigned_nested.add(id(cls))

                # Pass ONLY THIS text value's frames so nested answers are filtered correctly
                nested = _process_nested_classifications(
                    relevant_nested, parent_frame_tuples
                )
                if nested:
                    entry["classifications"] = nested

        results.append(entry)

    # Log orphaned nested classifications (not assigned to any parent)
    if all_nested_classifications:
        for cls in all_nested_classifications:
            if id(cls) not in assigned_nested:
                if isinstance(cls, TemporalClassificationText):
                    frames_info = cls.value[0][:2] if cls.value else "no frames"
                elif isinstance(cls, TemporalClassificationQuestion):
                    frames_info = (
                        cls.value[0].frames
                        if cls.value and cls.value[0].frames
                        else "no frames"
                    )
                else:
                    frames_info = "unknown"
                logger.warning(
                    f"Orphaned nested classification '{cls.name}' with frames {frames_info} - "
                    f"no parent text value found with overlapping frames."
                )

    return results


def _process_question_group(
    annotations: List[TemporalClassificationQuestion],
    parent_frames: List[Tuple[int, int]] = None,
) -> List[Dict[str, Any]]:
    """
    Process TemporalClassificationQuestion annotations.

    Each annotation has a list of TemporalClassificationAnswer objects.
    Groups by answer name and merges frames.

    Nested classifications are assigned to answers based on frame overlap.
    """
    # Collect all answers with their frames
    answer_data = defaultdict(lambda: {"frames": []})

    # Collect all nested classifications from all answers
    all_nested_by_answer = defaultdict(list)

    for ann in annotations:
        for answer in ann.value:  # value contains list of answers
            # Validate and collect frames
            valid_frames = []
            for start, end in answer.frames:
                # If parent_frames provided, check if answer frames are subset of ANY parent frame
                # A child frame is a subset if: parent_start <= child_start AND child_end <= parent_end
                if parent_frames:
                    is_valid = False
                    for parent_start, parent_end in parent_frames:
                        if parent_start <= start and end <= parent_end:
                            is_valid = True
                            break
                    if not is_valid:
                        # Don't log here - this is expected when processing inductive structures
                        # Only log orphaned classifications that are never assigned to any parent
                        continue
                valid_frames.append({"start": start, "end": end})

            if valid_frames:  # Only add if we have valid frames
                answer_data[answer.name]["frames"].extend(valid_frames)

                # Collect nested classifications at answer level
                if answer.classifications:
                    all_nested_by_answer[answer.name].extend(
                        answer.classifications
                    )

    # Track which nested classifications were assigned
    assigned_nested = set()

    # Build results
    results = []
    for answer_name, data in answer_data.items():
        # Deduplicate frames
        unique_frames = _deduplicate_frames(data["frames"])

        if not unique_frames:  # Skip if no valid frames
            continue

        entry = {
            "name": answer_name,
            "frames": unique_frames,
        }

        # Assign nested classifications based on frame overlap
        if all_nested_by_answer[answer_name]:
            parent_frame_tuples = [
                (f["start"], f["end"]) for f in unique_frames
            ]
            # Filter nested classifications that overlap with this answer's frames
            relevant_nested = _filter_classifications_by_overlap(
                all_nested_by_answer[answer_name], parent_frame_tuples
            )
            if relevant_nested:
                # Track that these were assigned
                for cls in relevant_nested:
                    assigned_nested.add(id(cls))

                nested = _process_nested_classifications(
                    relevant_nested, parent_frame_tuples
                )
                if nested:
                    entry["classifications"] = nested

        results.append(entry)

    # Log orphaned nested classifications (not assigned to any answer)
    for answer_name, nested_list in all_nested_by_answer.items():
        for cls in nested_list:
            if id(cls) not in assigned_nested:
                if isinstance(cls, TemporalClassificationText):
                    frames_info = cls.value[0][:2] if cls.value else "no frames"
                elif isinstance(cls, TemporalClassificationQuestion):
                    frames_info = (
                        cls.value[0].frames
                        if cls.value and cls.value[0].frames
                        else "no frames"
                    )
                else:
                    frames_info = "unknown"
                logger.warning(
                    f"Orphaned nested classification '{cls.name}' in answer '{answer_name}' with frames {frames_info} - "
                    f"no overlapping frames found with parent answer."
                )

    return results


def _process_nested_classifications(
    classifications: List[
        Union[TemporalClassificationText, TemporalClassificationQuestion]
    ],
    parent_frames: List[Tuple[int, int]],
) -> List[Dict[str, Any]]:
    """
    Process nested classifications recursively.

    Groups by name and processes each group.
    """
    # Group by name
    groups = defaultdict(list)
    for cls in classifications:
        groups[cls.name].append(cls)

    results = []
    for group_key, group_items in groups.items():
        # Get display name
        display_name = next((c.name for c in group_items if c.name), group_key)

        # Process based on type
        first_item = group_items[0]

        if isinstance(first_item, TemporalClassificationText):
            answers = _process_text_group(group_items, parent_frames)
        elif isinstance(first_item, TemporalClassificationQuestion):
            answers = _process_question_group(group_items, parent_frames)
        else:
            logger.warning(
                f"Unknown nested classification type: {type(first_item)}"
            )
            continue

        if answers:  # Only add if we have valid answers
            results.append(
                {
                    "name": display_name,
                    "answer": answers,
                }
            )

    return results


def _filter_classifications_by_overlap(
    classifications: List[
        Union[TemporalClassificationText, TemporalClassificationQuestion]
    ],
    parent_frames: List[Tuple[int, int]],
) -> List[Union[TemporalClassificationText, TemporalClassificationQuestion]]:
    """
    Filter classifications to only include those with frames that overlap with parent frames.

    A classification is included if ANY of its frame ranges overlap with ANY parent frame range.
    """
    relevant = []

    for cls in classifications:
        has_overlap = False

        # Check frames based on classification type
        if isinstance(cls, TemporalClassificationText):
            # Check text value frames
            for start, end, _ in cls.value:
                if _frames_overlap([(start, end)], parent_frames):
                    has_overlap = True
                    break
        elif isinstance(cls, TemporalClassificationQuestion):
            # Check answer frames
            for answer in cls.value:
                if _frames_overlap(answer.frames, parent_frames):
                    has_overlap = True
                    break

        if has_overlap:
            relevant.append(cls)

    return relevant


def _frames_overlap(
    frames1: List[Tuple[int, int]],
    frames2: List[Tuple[int, int]],
) -> bool:
    """
    Check if any frame in frames1 overlaps with any frame in frames2.

    Two frames (s1, e1) and (s2, e2) overlap if:
    max(s1, s2) <= min(e1, e2)
    """
    for start1, end1 in frames1:
        for start2, end2 in frames2:
            if max(start1, start2) <= min(end1, end2):
                return True
    return False


def _is_frame_subset(
    child_frames: List[Tuple[int, int]],
    parent_frames: List[Tuple[int, int]],
) -> bool:
    """
    Check if all child frames are subsets of at least one parent frame.

    A child frame (cs, ce) is a subset of parent frame (ps, pe) if:
    ps <= cs and ce <= pe
    """
    for child_start, child_end in child_frames:
        is_subset = False
        for parent_start, parent_end in parent_frames:
            if parent_start <= child_start and child_end <= parent_end:
                is_subset = True
                break

        if not is_subset:
            return False  # At least one child frame is not a subset

    return True


def _deduplicate_frames(frames: List[Dict[str, int]]) -> List[Dict[str, int]]:
    """
    Remove duplicate frame ranges.
    """
    seen = set()
    unique = []

    for frame in frames:
        frame_tuple = (frame["start"], frame["end"])
        if frame_tuple not in seen:
            seen.add(frame_tuple)
            unique.append(frame)

    return unique
