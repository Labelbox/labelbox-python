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
            first = anns[0]
            # Extract frames from each annotation (root frames)
            frames = [self.frame_extractor(a) for a in anns]
            frame_dicts = [{"start": start, "end": end} for start, end in frames]

            # Get root frames for passing to nested classifications
            root_frames = frames[0] if frames else (None, None)

            entry = self._create_answer_entry(first, frame_dicts, root_frames)
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
            # Default to root frames
            if root_frames and root_frames[0] is not None and root_frames[1] is not None:
                return [{"start": root_frames[0], "end": root_frames[1]}]
            else:
                # Fall back to parent frames if root not available
                return parent_frames

    def _create_answer_entry(self, first_ann: TemporalAnnotation, frames: List[Dict[str, int]], root_frames: Tuple[int, int]) -> Dict[str, Any]:
        """Create an answer entry from the first annotation and frames.

        Args:
            first_ann: The first annotation in the value group
            frames: List of frame dictionaries for this answer
            root_frames: Tuple of (start, end) from the root AudioClassificationAnnotation
        """
        if hasattr(first_ann.value, "answer") and isinstance(first_ann.value.answer, list):
            # Checklist: emit one entry per distinct option present in this bucket
            entries = []
            for opt in first_ann.value.answer:
                # Get frames for this specific checklist option (from opt or parent)
                opt_frames = self._get_nested_frames(opt, frames, root_frames)
                entry = {"name": opt.name, "frames": opt_frames}
                # Handle explicit nesting for this checklist option
                if hasattr(opt, 'classifications') and opt.classifications:
                    entry["classifications"] = self._serialize_explicit_classifications(opt.classifications, root_frames)
                entries.append(entry)
            return entries[0] if len(entries) == 1 else {"options": entries, "frames": frames}
        elif hasattr(first_ann.value, "answer") and hasattr(first_ann.value.answer, "name"):
            # Radio
            opt = first_ann.value.answer
            # Get frames for this radio answer (from answer or parent)
            opt_frames = self._get_nested_frames(opt, frames, root_frames)
            entry = {"name": opt.name, "frames": opt_frames}
            # Handle explicit nesting via ClassificationAnswer.classifications
            if hasattr(opt, 'classifications') and opt.classifications:
                entry["classifications"] = self._serialize_explicit_classifications(opt.classifications, root_frames)
            return entry
        else:
            # Text - nesting is at the annotation level, not answer level
            entry = {"value": first_ann.value.answer, "frames": frames}
            # Handle explicit nesting via AudioClassificationAnnotation.classifications
            if hasattr(first_ann, 'classifications') and first_ann.classifications:
                entry["classifications"] = self._serialize_explicit_classifications(first_ann.classifications, root_frames)
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
            answers = []
            for cls in cls_list:
                # Get frames for this ClassificationAnnotation (from cls or root)
                cls_frames = self._get_nested_frames(cls, [], root_frames)

                if hasattr(cls.value, "answer"):
                    if isinstance(cls.value.answer, list):
                        # Checklist
                        for opt in cls.value.answer:
                            # Get frames for this checklist option (from opt or cls or root)
                            opt_frames = self._get_nested_frames(opt, cls_frames, root_frames)
                            answer = {"name": opt.name, "frames": opt_frames}
                            # Recursively handle deeper nesting
                            if hasattr(opt, 'classifications') and opt.classifications:
                                answer["classifications"] = self._serialize_explicit_classifications(opt.classifications, root_frames)
                            answers.append(answer)
                    elif hasattr(cls.value.answer, "name"):
                        # Radio
                        opt = cls.value.answer
                        # Get frames for this radio answer (from opt or cls or root)
                        opt_frames = self._get_nested_frames(opt, cls_frames, root_frames)
                        answer = {"name": opt.name, "frames": opt_frames}
                        # Recursively handle deeper nesting
                        if hasattr(opt, 'classifications') and opt.classifications:
                            answer["classifications"] = self._serialize_explicit_classifications(opt.classifications, root_frames)
                        answers.append(answer)
                    else:
                        # Text - check for annotation-level nesting
                        answer = {"value": cls.value.answer, "frames": cls_frames}
                        # Recursively handle deeper nesting at ClassificationAnnotation level
                        if hasattr(cls, 'classifications') and cls.classifications:
                            answer["classifications"] = self._serialize_explicit_classifications(cls.classifications, root_frames)
                        answers.append(answer)

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
