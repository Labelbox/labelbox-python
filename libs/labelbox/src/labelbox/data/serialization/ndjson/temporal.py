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
    TemporalClassificationAnswer,
)

logger = logging.getLogger(__name__)


class TemporalNDJSON(BaseModel):
    """NDJSON structure for temporal annotations"""

    name: str
    answer: List[Dict[str, Any]]
    dataRow: Dict[str, str]


def create_temporal_ndjson_annotations(
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

    # Group by classification name/schema_id
    groups = defaultdict(list)
    for ann in annotations:
        key = ann.feature_schema_id or ann.name
        groups[key].append(ann)

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
            logger.warning(f"Unknown temporal annotation type: {type(first_ann)}")
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
    """
    # Collect all text values with their frames
    text_data = defaultdict(lambda: {"frames": [], "nested": []})

    for ann in annotations:
        for start, end, text_value in ann.value:
            # Validate frames against parent if provided
            if parent_frames and not _is_frame_subset([(start, end)], parent_frames):
                logger.warning(
                    f"Text value frames ({start}, {end}) not subset of parent frames {parent_frames}. Discarding."
                )
                continue

            text_data[text_value]["frames"].append({"start": start, "end": end})

            # Collect nested classifications
            if ann.classifications:
                text_data[text_value]["nested"].extend(ann.classifications)

    # Build results
    results = []
    for text_value, data in text_data.items():
        # Deduplicate frames
        unique_frames = _deduplicate_frames(data["frames"])

        entry = {
            "value": text_value,
            "frames": unique_frames,
        }

        # Process nested classifications recursively
        if data["nested"]:
            parent_frame_tuples = [(f["start"], f["end"]) for f in unique_frames]
            nested = _process_nested_classifications(data["nested"], parent_frame_tuples)
            if nested:
                entry["classifications"] = nested

        results.append(entry)

    return results


def _process_question_group(
    annotations: List[TemporalClassificationQuestion],
    parent_frames: List[Tuple[int, int]] = None,
) -> List[Dict[str, Any]]:
    """
    Process TemporalClassificationQuestion annotations.

    Each annotation has a list of TemporalClassificationAnswer objects.
    Groups by answer name and merges frames.
    """
    # Collect all answers
    answer_data = defaultdict(lambda: {"frames": [], "nested": []})

    for ann in annotations:
        for answer in ann.value:  # value contains list of answers
            # Validate and collect frames
            valid_frames = []
            for start, end in answer.frames:
                if parent_frames and not _is_frame_subset([(start, end)], parent_frames):
                    logger.warning(
                        f"Answer '{answer.name}' frames ({start}, {end}) not subset of parent frames {parent_frames}. Discarding."
                    )
                    continue
                valid_frames.append({"start": start, "end": end})

            if valid_frames:  # Only add if we have valid frames
                answer_data[answer.name]["frames"].extend(valid_frames)

                # Collect nested classifications
                if answer.classifications:
                    answer_data[answer.name]["nested"].extend(answer.classifications)

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

        # Process nested classifications recursively
        if data["nested"]:
            parent_frame_tuples = [(f["start"], f["end"]) for f in unique_frames]
            nested = _process_nested_classifications(data["nested"], parent_frame_tuples)
            if nested:
                entry["classifications"] = nested

        results.append(entry)

    return results


def _process_nested_classifications(
    classifications: List[Union[TemporalClassificationText, TemporalClassificationQuestion]],
    parent_frames: List[Tuple[int, int]],
) -> List[Dict[str, Any]]:
    """
    Process nested classifications recursively.

    Groups by name/schema_id and processes each group.
    """
    # Group by name
    groups = defaultdict(list)
    for cls in classifications:
        key = cls.feature_schema_id or cls.name
        groups[key].append(cls)

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
            logger.warning(f"Unknown nested classification type: {type(first_item)}")
            continue

        if answers:  # Only add if we have valid answers
            results.append({
                "name": display_name,
                "answer": answers,
            })

    return results


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
