"""
Generic hierarchical classification builder for NDJSON serialization.

This module provides reusable components for constructing nested hierarchical
classifications from temporal annotations (audio, video, etc.), separating the 
complex logic from the main serialization code.
"""

from collections import defaultdict
from typing import Any, Dict, List, Set, Tuple, Protocol, TypeVar, Generic
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
    """Manages grouping of temporal annotations by classification type."""
    
    def __init__(self, annotations: List[TemporalAnnotation], frame_extractor: callable):
        self.annotations = annotations
        self.frame_extractor = frame_extractor  # Function to extract (start, end) from annotation
        self.groups = self._group_annotations()
        self.root_groups = self._identify_root_groups()
    
    def _group_annotations(self) -> Dict[str, List[TemporalAnnotation]]:
        """Group annotations by classification key (schema_id or name)."""
        groups = defaultdict(list)
        for annot in self.annotations:
            key = annot.feature_schema_id or annot.name
            groups[key].append(annot)
        return dict(groups)
    
    def _identify_root_groups(self) -> Set[str]:
        """Identify root groups that are not fully contained by other groups."""
        root_groups = set()
        
        for group_key, group_anns in self.groups.items():
            if not self._is_group_nested(group_key):
                root_groups.add(group_key)
        
        return root_groups
    
    def _is_group_nested(self, group_key: str) -> bool:
        """Check if a group is fully contained by other groups."""
        group_anns = self.groups[group_key]
        
        for ann in group_anns:
            start, end = self.frame_extractor(ann)
            ann_frame = TemporalFrame(start, end)
            
            # Check if this annotation is contained by any other group
            contained = False
            for other_key, other_anns in self.groups.items():
                if other_key == group_key:
                    continue
                
                for parent in other_anns:
                    parent_start, parent_end = self.frame_extractor(parent)
                    parent_frame = TemporalFrame(parent_start, parent_end)
                    if parent_frame.contains(ann_frame):
                        contained = True
                        break
                
                if contained:
                    break
            
            if not contained:
                return False  # Group is not fully nested
        
        return True  # All annotations were contained somewhere
    
    def get_group_display_name(self, group_key: str) -> str:
        """Get display name for a group."""
        group_anns = self.groups[group_key]
        # Prefer the first non-empty annotation name
        for ann in group_anns:
            if ann.name:
                return ann.name
        return group_key
    
    def get_annotations_within_frames(self, frames: List[TemporalFrame], exclude_group: str = None) -> List[TemporalAnnotation]:
        """Get all annotations within the given frames, excluding specified group."""
        contained = []
        
        for group_key, group_anns in self.groups.items():
            if group_key == exclude_group:
                continue
            
            for ann in group_anns:
                start, end = self.frame_extractor(ann)
                ann_frame = TemporalFrame(start, end)
                if any(frame.contains(ann_frame) for frame in frames):
                    contained.append(ann)
        
        return contained


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
            frames = [self.frame_extractor(a) for a in anns]
            frame_dicts = [{"start": start, "end": end} for start, end in frames]
            
            entry = self._create_answer_entry(first, frame_dicts)
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
    
    def _create_answer_entry(self, first_ann: TemporalAnnotation, frames: List[Dict[str, int]]) -> Dict[str, Any]:
        """Create an answer entry from the first annotation and frames."""
        if hasattr(first_ann.value, "answer") and isinstance(first_ann.value.answer, list):
            # Checklist: emit one entry per distinct option present in this bucket
            entries = []
            for opt_name in sorted([o.name for o in first_ann.value.answer]):
                entries.append({"name": opt_name, "frames": frames})
            return entries[0] if len(entries) == 1 else {"options": entries, "frames": frames}
        elif hasattr(first_ann.value, "answer") and hasattr(first_ann.value.answer, "name"):
            # Radio
            return {"name": first_ann.value.answer.name, "frames": frames}
        else:
            # Text
            return {"value": first_ann.value.answer, "frames": frames}


class HierarchyBuilder(Generic[TemporalAnnotation]):
    """Builds hierarchical nested classifications from temporal annotations."""
    
    def __init__(self, group_manager: AnnotationGroupManager[TemporalAnnotation], value_grouper: ValueGrouper[TemporalAnnotation]):
        self.group_manager = group_manager
        self.value_grouper = value_grouper
    
    def build_hierarchy(self) -> List[Dict[str, Any]]:
        """Build the complete hierarchical structure."""
        results = []
        
        for group_key in self.group_manager.root_groups:
            group_anns = self.group_manager.groups[group_key]
            top_entries = self.value_grouper.group_by_value(group_anns)
            
            # Attach nested classifications to each top-level entry
            for entry in top_entries:
                frames = [TemporalFrame(f["start"], f["end"]) for f in entry.get("frames", [])]
                nested = self._build_nested_for_frames(frames, group_key)
                if nested:
                    entry["classifications"] = nested
            
            results.append({
                "name": self.group_manager.get_group_display_name(group_key),
                "answer": top_entries,
            })
        
        return results
    
    def _build_nested_for_frames(self, parent_frames: List[TemporalFrame], exclude_group: str) -> List[Dict[str, Any]]:
        """Recursively build nested classifications for specific parent frames."""
        nested = []
        
        # Get all annotations within parent frames
        all_contained = self.group_manager.get_annotations_within_frames(parent_frames, exclude_group)
        
        # Group by classification type and process each group
        for group_key, group_anns in self.group_manager.groups.items():
            if group_key == exclude_group or group_key in self.group_manager.root_groups:
                continue
            
            # Filter annotations that are contained by parent frames
            candidate_anns = []
            for ann in group_anns:
                start, end = self.group_manager.frame_extractor(ann)
                ann_frame = TemporalFrame(start, end)
                if any(frame.contains(ann_frame) for frame in parent_frames):
                    candidate_anns.append(ann)
            
            if not candidate_anns:
                continue
            
            # Keep only immediate children (not strictly contained by other contained annotations)
            child_anns = self._filter_immediate_children(candidate_anns, all_contained)
            if not child_anns:
                continue
            
            # Build this child classification block
            child_entries = self.value_grouper.group_by_value(child_anns)
            
            # Recursively attach further nested classifications
            for entry in child_entries:
                entry_frames = [TemporalFrame(f["start"], f["end"]) for f in entry.get("frames", [])]
                child_nested = self._build_nested_for_frames(entry_frames, group_key)
                if child_nested:
                    entry["classifications"] = child_nested
            
            nested.append({
                "name": self.group_manager.get_group_display_name(group_key),
                "answer": child_entries,
            })
        
        return nested
    
    def _filter_immediate_children(self, candidates: List[TemporalAnnotation], 
                                 all_contained: List[TemporalAnnotation]) -> List[TemporalAnnotation]:
        """Filter to keep only immediate children (not strictly contained by others)."""
        immediate_children = []
        
        for candidate in candidates:
            start, end = self.group_manager.frame_extractor(candidate)
            candidate_frame = TemporalFrame(start, end)
            
            # Check if this candidate is strictly contained by any other contained annotation
            has_closer_container = False
            for other in all_contained:
                if other is candidate:
                    continue
                other_start, other_end = self.group_manager.frame_extractor(other)
                other_frame = TemporalFrame(other_start, other_end)
                if other_frame.strictly_contains(candidate_frame):
                    has_closer_container = True
                    break
            
            if not has_closer_container:
                immediate_children.append(candidate)
        
        return immediate_children


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
