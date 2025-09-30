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
        self.parent_assignments = self._compute_parent_assignments()

    def _compute_parent_assignments(self) -> Dict[str, str]:
        """
        Compute best parent assignment for each group based on temporal containment and hierarchy depth.
        Returns mapping of child_group_key -> parent_group_key.
        """
        assignments = {}
        assignment_depth = {}  # Track depth of each assignment (0 = root)

        # Assign depth 0 to roots
        for root_key in self.group_manager.root_groups:
            assignment_depth[root_key] = 0

        # Build assignments level by level
        remaining_groups = set(self.group_manager.groups.keys()) - self.group_manager.root_groups

        max_iterations = len(remaining_groups) + 1  # Prevent infinite loops
        iteration = 0

        while remaining_groups and iteration < max_iterations:
            iteration += 1
            assigned_this_round = set()

            for child_key in remaining_groups:
                child_anns = self.group_manager.groups[child_key]

                # Find all potential parents (groups that contain this child's annotations)
                potential_parents = []

                for parent_key, parent_anns in self.group_manager.groups.items():
                    if parent_key == child_key:
                        continue

                    # Check if all child annotations are contained by at least one parent annotation
                    all_contained = True
                    for child_ann in child_anns:
                        child_start, child_end = self.group_manager.frame_extractor(child_ann)
                        child_frame = TemporalFrame(child_start, child_end)

                        contained_by_parent = False
                        for parent_ann in parent_anns:
                            parent_start, parent_end = self.group_manager.frame_extractor(parent_ann)
                            parent_frame = TemporalFrame(parent_start, parent_end)
                            if parent_frame.contains(child_frame):
                                contained_by_parent = True
                                break

                        if not contained_by_parent:
                            all_contained = False
                            break

                    if all_contained:
                        # Calculate average container size for this parent
                        avg_size = sum((self.group_manager.frame_extractor(ann)[1] - self.group_manager.frame_extractor(ann)[0])
                                       for ann in parent_anns) / len(parent_anns)

                        # Get depth of this parent (lower depth = closer to root = prefer)
                        parent_depth = assignment_depth.get(parent_key, 999)

                        # Name similarity heuristic: if child name contains parent name as prefix/substring,
                        # it's likely related (e.g., "sub_radio_question_2" contains "sub_radio_question")
                        name_similarity = 1 if parent_key in child_key else 0

                        potential_parents.append((parent_key, avg_size, parent_depth, name_similarity))

                # Choose best parent: prefer name similarity, then higher depth, then smallest size
                if potential_parents:
                    # Sort by: 1) prefer name similarity, 2) prefer higher depth, 3) smallest size
                    potential_parents.sort(key=lambda x: (-x[3], -x[2], x[1]))
                    best_parent = potential_parents[0][0]
                    assignments[child_key] = best_parent
                    assignment_depth[child_key] = assignment_depth.get(best_parent, 0) + 1
                    assigned_this_round.add(child_key)

            # Remove assigned groups from remaining
            remaining_groups -= assigned_this_round

            # If no progress, break to avoid infinite loop
            if not assigned_this_round:
                break

        return assignments

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
    
    def _build_nested_for_frames(self, parent_frames: List[TemporalFrame], parent_group_key: str) -> List[Dict[str, Any]]:
        """Recursively build nested classifications for specific parent frames."""
        nested = []

        # Get all annotations within parent frames
        all_contained = self.group_manager.get_annotations_within_frames(parent_frames, parent_group_key)

        # Group by classification type and process each group
        for group_key, group_anns in self.group_manager.groups.items():
            if group_key == parent_group_key or group_key in self.group_manager.root_groups:
                continue

            # Only process groups that are assigned to this parent
            if self.parent_assignments.get(group_key) != parent_group_key:
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
