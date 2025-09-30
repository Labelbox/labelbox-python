"""
Generic hierarchical classification builder for NDJSON serialization.

This module provides reusable components for constructing nested hierarchical
classifications from temporal annotations (audio, video, etc.).

IMPORTANT: This module ONLY supports explicit nesting via ClassificationAnswer.classifications.
Annotations must define their hierarchy structure explicitly in the annotation objects.
Temporal containment-based inference is NOT supported.
"""

from collections import defaultdict
from typing import Any, Dict, List, Tuple, TypeVar, Generic
from pydantic import BaseModel

from ...annotation_types.audio import AudioClassificationAnnotation

# Generic type for temporal annotations
TemporalAnnotation = TypeVar('TemporalAnnotation', bound=Any)


class TemporalFrame:
    """Represents a time frame in temporal annotations (audio, video, etc.)."""
    
    def __init__(self, start: int, end: int = None):
        self.start = start
        self.end = end or start
    
    def contains(self, other: "TemporalFrame") -> bool:
        """Check if this frame contains another frame."""
        return (self.start <= other.start and 
                self.end is not None and other.end is not None and 
                self.end >= other.end)
    
    def strictly_contains(self, other: "TemporalFrame") -> bool:
        """Check if this frame strictly contains another frame (not equal)."""
        return (self.contains(other) and 
                (self.start < other.start or self.end > other.end))
    
    def overlaps(self, other: "TemporalFrame") -> bool:
        """Check if this frame overlaps with another frame."""
        return not (self.end < other.start or other.end < self.start)
    
    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary format."""
        return {"start": self.start, "end": self.end}


class AnnotationGroupManager(Generic[TemporalAnnotation]):
    """Manages grouping of temporal annotations by classification type.

    NOTE: Since we only support explicit nesting via ClassificationAnswer.classifications,
    all top-level AudioClassificationAnnotation objects are considered roots.
    """

    def __init__(self, annotations: List[TemporalAnnotation], frame_extractor: callable):
        self.annotations = annotations
        self.frame_extractor = frame_extractor  # Function to extract (start, end) from annotation
        self.groups = self._group_annotations()
        self.root_groups = set(self.groups.keys())  # All groups are roots with explicit nesting

    def _group_annotations(self) -> Dict[str, List[TemporalAnnotation]]:
        """Group annotations by classification key (schema_id or name)."""
        groups = defaultdict(list)
        for annot in self.annotations:
            key = annot.feature_schema_id or annot.name
            groups[key].append(annot)
        return dict(groups)

    def get_group_display_name(self, group_key: str) -> str:
        """Get display name for a group."""
        group_anns = self.groups[group_key]
        # Prefer the first non-empty annotation name
        for ann in group_anns:
            if ann.name:
                return ann.name
        return group_key


class ValueGrouper(Generic[TemporalAnnotation]):
    """Handles grouping of annotations by their values and answer construction."""

    def __init__(self, frame_extractor: callable):
        self.frame_extractor = frame_extractor  # Function to extract (start, end) from annotation

    def group_by_value(self, annotations: List[TemporalAnnotation]) -> List[Dict[str, Any]]:
        """Group annotations by logical value and produce answer entries."""
        value_buckets = defaultdict(list)

        for ann in annotations:
            key = self._get_value_key(ann)
            value_buckets[key].append(ann)

        entries = []
        for _, anns in value_buckets.items():
            # Extract frames from each annotation (root frames)
            frames = [self.frame_extractor(a) for a in anns]
            frame_dicts = [{"start": start, "end": end} for start, end in frames]

            # Get root frames for passing to nested classifications (use first annotation's frames)
            root_frames = frames[0] if frames else (None, None)

            # Pass ALL annotations so we can merge their nested classifications
            entry = self._create_answer_entry(anns, frame_dicts, root_frames)
            entries.append(entry)

        return entries
    
    def _get_value_key(self, ann: TemporalAnnotation) -> str:
        """Get a stable key for grouping annotations by value."""
        if hasattr(ann.value, "answer"):
            if isinstance(ann.value.answer, list):
                # Checklist: stable key from selected option names
                return str(sorted([opt.name for opt in ann.value.answer]))
            elif hasattr(ann.value.answer, "name"):
                # Radio: option name
                return ann.value.answer.name
            else:
                # Text: the string value
                return ann.value.answer
        else:
            return str(ann.value)
    
    def _get_nested_frames(self, obj: Any, parent_frames: List[Dict[str, int]], root_frames: Tuple[int, int]) -> List[Dict[str, int]]:
        """Get frame range for nested classification object.

        If obj has start_frame/end_frame specified, use those. Otherwise default to root frames.

        Args:
            obj: ClassificationAnswer or ClassificationAnnotation
            parent_frames: Parent's frame list (for fallback)
            root_frames: Root annotation's (start, end) tuple

        Returns:
            List of frame dictionaries
        """
        if hasattr(obj, 'start_frame') and obj.start_frame is not None and hasattr(obj, 'end_frame') and obj.end_frame is not None:
            # Use explicitly specified frames
            return [{"start": obj.start_frame, "end": obj.end_frame}]
        else:
            # Default to parent frames first, then root frames
            if parent_frames:
                return parent_frames
            elif root_frames and root_frames[0] is not None and root_frames[1] is not None:
                return [{"start": root_frames[0], "end": root_frames[1]}]
            else:
                return []

    def _create_answer_entry(self, anns: List[TemporalAnnotation], frames: List[Dict[str, int]], root_frames: Tuple[int, int]) -> Dict[str, Any]:
        """Create an answer entry from all annotations with the same value, merging their nested classifications.

        Args:
            anns: All annotations in the value group
            frames: List of frame dictionaries for this answer
            root_frames: Tuple of (start, end) from the root AudioClassificationAnnotation
        """
        first_ann = anns[0]

        if hasattr(first_ann.value, "answer") and isinstance(first_ann.value.answer, list):
            # Checklist: emit one entry per distinct option present across ALL annotations
            # First, collect all unique option names across all annotations
            all_option_names = set()
            for ann in anns:
                if hasattr(ann.value, "answer") and isinstance(ann.value.answer, list):
                    for opt in ann.value.answer:
                        all_option_names.add(opt.name)

            entries = []
            for opt_name in sorted(all_option_names):  # Sort for consistent ordering
                # For each unique option, collect frames and nested classifications from all annotations
                opt_frames = []
                all_nested = []
                for ann in anns:
                    if hasattr(ann.value, "answer") and isinstance(ann.value.answer, list):
                        for ann_opt in ann.value.answer:
                            if ann_opt.name == opt_name:
                                # Get this annotation's root frame range
                                ann_start, ann_end = self.frame_extractor(ann)
                                ann_frame_dict = [{"start": ann_start, "end": ann_end}]
                                # Collect this option's frame range (from option or parent annotation)
                                frames_for_this_opt = self._get_nested_frames(ann_opt, ann_frame_dict, root_frames)
                                opt_frames.extend(frames_for_this_opt)
                                # Collect nested classifications
                                if hasattr(ann_opt, 'classifications') and ann_opt.classifications:
                                    all_nested.extend(ann_opt.classifications)

                entry = {"name": opt_name, "frames": opt_frames}
                if all_nested:
                    entry["classifications"] = self._serialize_explicit_classifications(all_nested, root_frames)
                entries.append(entry)
            return entries[0] if len(entries) == 1 else {"options": entries, "frames": frames}
        elif hasattr(first_ann.value, "answer") and hasattr(first_ann.value.answer, "name"):
            # Radio
            opt = first_ann.value.answer
            # Use the merged frames from all annotations (already passed in)
            entry = {"name": opt.name, "frames": frames}
            # Collect nested classifications from all annotations
            all_nested = []
            for ann in anns:
                if hasattr(ann.value, "answer") and hasattr(ann.value.answer, "classifications") and ann.value.answer.classifications:
                    all_nested.extend(ann.value.answer.classifications)
            if all_nested:
                entry["classifications"] = self._serialize_explicit_classifications(all_nested, root_frames)
            return entry
        else:
            # Text - nesting is at the annotation level, not answer level
            entry = {"value": first_ann.value.answer, "frames": frames}
            # Collect nested classifications from all annotations
            all_nested = []
            for ann in anns:
                if hasattr(ann, 'classifications') and ann.classifications:
                    all_nested.extend(ann.classifications)
            if all_nested:
                entry["classifications"] = self._serialize_explicit_classifications(all_nested, root_frames)
            return entry

    def _serialize_explicit_classifications(self, classifications: List[Any], root_frames: Tuple[int, int]) -> List[Dict[str, Any]]:
        """Serialize explicitly nested ClassificationAnnotation objects.

        Args:
            classifications: List of ClassificationAnnotation objects
            root_frames: Tuple of (start, end) from root AudioClassificationAnnotation

        Returns:
            List of serialized classification dictionaries
        """
        result = []

        # Group nested classifications by name
        grouped = defaultdict(list)
        for cls in classifications:
            name = cls.feature_schema_id or cls.name
            grouped[name].append(cls)

        # Serialize each group
        for name, cls_list in grouped.items():
            # Get display name from first annotation
            display_name = cls_list[0].name if cls_list[0].name else name

            # Create answer entries for this nested classification
            # De-duplicate by answer value
            seen_values = {}  # value_key -> (answer_dict, nested_classifications)
            for cls in cls_list:
                # Get frames for this ClassificationAnnotation (from cls or root)
                cls_frames = self._get_nested_frames(cls, [], root_frames)
                value_key = self._get_value_key(cls)

                if hasattr(cls.value, "answer"):
                    if isinstance(cls.value.answer, list):
                        # Checklist
                        for opt in cls.value.answer:
                            # Get frames for this checklist option (from opt or cls or root)
                            opt_frames = self._get_nested_frames(opt, cls_frames, root_frames)
                            answer = {"name": opt.name, "frames": opt_frames}
                            # Collect nested for recursion
                            opt_nested = []
                            if hasattr(opt, 'classifications') and opt.classifications:
                                opt_nested = opt.classifications
                            if opt_nested:
                                answer["classifications"] = self._serialize_explicit_classifications(opt_nested, root_frames)
                            # Note: Checklist options don't need de-duplication
                            # (they're already handled at the parent level)
                            if value_key not in seen_values:
                                seen_values[value_key] = []
                            seen_values[value_key].append(answer)
                    elif hasattr(cls.value.answer, "name"):
                        # Radio - de-duplicate by name
                        opt = cls.value.answer
                        # Check if this answer has explicit frames
                        has_explicit_frames = (hasattr(opt, 'start_frame') and opt.start_frame is not None and
                                             hasattr(opt, 'end_frame') and opt.end_frame is not None)
                        # Get frames for this radio answer (from opt or cls or root)
                        opt_frames = self._get_nested_frames(opt, cls_frames, root_frames)

                        # Check if we've already seen this answer name
                        if value_key in seen_values:
                            # Only merge frames if both have explicit frames, or neither does
                            existing_has_explicit = seen_values[value_key].get("_has_explicit", False)
                            if has_explicit_frames and existing_has_explicit:
                                # Both explicit - merge
                                seen_values[value_key]["frames"].extend(opt_frames)
                            elif has_explicit_frames and not existing_has_explicit:
                                # Current is explicit, existing is implicit - replace with explicit
                                seen_values[value_key]["frames"] = opt_frames
                                seen_values[value_key]["_has_explicit"] = True
                            elif not has_explicit_frames and existing_has_explicit:
                                # Current is implicit, existing is explicit - keep existing (don't merge)
                                pass
                            else:
                                # Both implicit - merge
                                seen_values[value_key]["frames"].extend(opt_frames)

                            # Always merge nested classifications
                            if hasattr(opt, 'classifications') and opt.classifications:
                                seen_values[value_key]["_nested"].extend(opt.classifications)
                        else:
                            answer = {"name": opt.name, "frames": opt_frames, "_nested": [], "_has_explicit": has_explicit_frames}
                            if hasattr(opt, 'classifications') and opt.classifications:
                                answer["_nested"] = list(opt.classifications)
                            seen_values[value_key] = answer
                    else:
                        # Text - check for annotation-level nesting
                        answer = {"value": cls.value.answer, "frames": cls_frames}
                        # Collect nested
                        text_nested = []
                        if hasattr(cls, 'classifications') and cls.classifications:
                            text_nested = cls.classifications
                        if text_nested:
                            answer["classifications"] = self._serialize_explicit_classifications(text_nested, root_frames)
                        if value_key not in seen_values:
                            seen_values[value_key] = []
                        seen_values[value_key].append(answer)

            # Convert seen_values to answers list
            answers = []
            for value_key, value_data in seen_values.items():
                if isinstance(value_data, list):
                    answers.extend(value_data)
                else:
                    # Radio case - handle nested classifications
                    if value_data.get("_nested"):
                        value_data["classifications"] = self._serialize_explicit_classifications(value_data["_nested"], root_frames)
                    # Clean up internal fields
                    value_data.pop("_nested", None)
                    value_data.pop("_has_explicit", None)
                    answers.append(value_data)

            result.append({
                "name": display_name,
                "answer": answers
            })

        return result


class HierarchyBuilder(Generic[TemporalAnnotation]):
    """Builds hierarchical nested classifications from temporal annotations.

    NOTE: This builder only handles explicit nesting via ClassificationAnswer.classifications.
    All nesting must be defined in the annotation structure itself, not inferred from temporal containment.
    """

    def __init__(self, group_manager: AnnotationGroupManager[TemporalAnnotation], value_grouper: ValueGrouper[TemporalAnnotation]):
        self.group_manager = group_manager
        self.value_grouper = value_grouper

    def build_hierarchy(self) -> List[Dict[str, Any]]:
        """Build the complete hierarchical structure.

        All nesting is handled via explicit ClassificationAnswer.classifications,
        so we simply group by value and let the ValueGrouper serialize the nested structure.
        """
        results = []

        for group_key in self.group_manager.root_groups:
            group_anns = self.group_manager.groups[group_key]
            top_entries = self.value_grouper.group_by_value(group_anns)

            results.append({
                "name": self.group_manager.get_group_display_name(group_key),
                "answer": top_entries,
            })

        return results


class TemporalNDJSON(BaseModel):
    """NDJSON format for temporal annotations (audio, video, etc.)."""
    name: str
    answer: List[Dict[str, Any]]
    dataRow: Dict[str, str]


def create_temporal_ndjson_annotations(annotations: List[TemporalAnnotation], 
                                     data_global_key: str,
                                     frame_extractor: callable) -> List[TemporalNDJSON]:
    """
    Create NDJSON temporal annotations with hierarchical structure.
    
    Args:
        annotations: List of temporal classification annotations
        data_global_key: Global key for the data row
        frame_extractor: Function that extracts (start, end) from annotation
        
    Returns:
        List of TemporalNDJSON objects
    """
    if not annotations:
        return []
    
    group_manager = AnnotationGroupManager(annotations, frame_extractor)
    value_grouper = ValueGrouper(frame_extractor)
    hierarchy_builder = HierarchyBuilder(group_manager, value_grouper)
    hierarchy = hierarchy_builder.build_hierarchy()
    
    return [
        TemporalNDJSON(
            name=item["name"],
            answer=item["answer"],
            dataRow={"globalKey": data_global_key}
        )
        for item in hierarchy
    ]


# Audio-specific convenience function
def create_audio_ndjson_annotations(annotations: List[AudioClassificationAnnotation], 
                                  data_global_key: str) -> List[TemporalNDJSON]:
    """
    Create NDJSON audio annotations with hierarchical structure.
    
    Args:
        annotations: List of audio classification annotations
        data_global_key: Global key for the data row
        
    Returns:
        List of TemporalNDJSON objects
    """
    def audio_frame_extractor(ann: AudioClassificationAnnotation) -> Tuple[int, int]:
        return (ann.start_frame, ann.end_frame or ann.start_frame)
    
    return create_temporal_ndjson_annotations(annotations, data_global_key, audio_frame_extractor)
