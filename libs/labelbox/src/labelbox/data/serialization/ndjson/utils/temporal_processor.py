"""
Generic temporal annotation processor for frame-based media (video, audio)
"""

from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, Dict, Generator, List, Union

from ....annotation_types.label import Label
from ..classification import NDClassificationType, NDClassification
from ..objects import NDObject


class TemporalAnnotationProcessor(ABC):
    """Abstract base class for processing temporal annotations (video, audio, etc.)"""

    @abstractmethod
    def get_annotation_types(self) -> tuple:
        """Return tuple of annotation types this processor handles"""
        pass

    @abstractmethod
    def should_group_annotations(self, annotation_group: List) -> bool:
        """Determine if annotations should be grouped into one feature"""
        pass

    @abstractmethod
    def build_frame_data(self, annotation_group: List) -> List[Dict[str, Any]]:
        """Extract frame data from annotation group"""
        pass

    @abstractmethod
    def prepare_grouped_content(self, annotation_group: List) -> Any:
        """Prepare content for grouped annotations (may modify annotation.value)"""
        pass

    def process_annotations(
        self, label: Label
    ) -> Generator[Union[NDClassificationType, Any], None, None]:
        """Main processing method - generic for all temporal media"""
        temporal_annotations = defaultdict(list)
        classification_types, object_types = self.get_annotation_types()

        # Group annotations by feature name/schema
        for annot in label.annotations:
            if isinstance(annot, classification_types + object_types):
                temporal_annotations[
                    annot.feature_schema_id or annot.name
                ].append(annot)

        # Process each group
        for annotation_group in temporal_annotations.values():
            if isinstance(annotation_group[0], classification_types):
                yield from self._process_classification_group(
                    annotation_group, label.data
                )
            elif isinstance(annotation_group[0], object_types):
                yield from self._process_object_group(
                    annotation_group, label.data
                )

    def _process_classification_group(self, annotation_group, data):
        """Process classification annotations"""
        if self.should_group_annotations(annotation_group):
            # Group into single feature with multiple keyframes
            annotation = annotation_group[0]  # Use first as template

            # Build frame data
            frames_data = self.build_frame_data(annotation_group)

            # Prepare content (may modify annotation.value)
            self.prepare_grouped_content(annotation_group)

            # Update with frame data
            annotation.extra = {"frames": frames_data}
            yield NDClassification.from_common(annotation, data)
        else:
            # Process individually
            for annotation in annotation_group:
                frames_data = self.build_frame_data([annotation])
                if frames_data:
                    if not annotation.extra:
                        annotation.extra = {}
                    annotation.extra.update({"frames": frames_data})
                yield NDClassification.from_common(annotation, data)

    def _process_object_group(self, annotation_group, data):
        """Process object annotations - default to individual processing"""
        for annotation in annotation_group:
            yield NDObject.from_common(annotation, data)


class AudioTemporalProcessor(TemporalAnnotationProcessor):
    """Processor for audio temporal annotations"""

    def __init__(
        self,
        group_text_annotations: bool = True,
        enable_token_mapping: bool = True,
    ):
        self.group_text_annotations = group_text_annotations
        self.enable_token_mapping = enable_token_mapping

    def get_annotation_types(self) -> tuple:
        from ....annotation_types.audio import (
            AudioClassificationAnnotation,
            AudioObjectAnnotation,
        )

        return (AudioClassificationAnnotation,), (AudioObjectAnnotation,)

    def should_group_annotations(self, annotation_group: List) -> bool:
        """Group TEXT classifications with multiple temporal instances"""
        if not self.group_text_annotations:
            return False

        from ....annotation_types.classification.classification import Text

        return (
            isinstance(annotation_group[0].value, Text)
            and len(annotation_group) > 1
            and all(hasattr(ann, "frame") for ann in annotation_group)
        )

    def build_frame_data(self, annotation_group: List) -> List[Dict[str, Any]]:
        """Extract frame ranges from audio annotations"""
        frames_data = []
        for annotation in annotation_group:
            if hasattr(annotation, "frame"):
                frame = annotation.frame
                end_frame = (
                    annotation.end_frame
                    if hasattr(annotation, "end_frame")
                    and annotation.end_frame is not None
                    else frame
                )
                frames_data.append({"start": frame, "end": end_frame})
        return frames_data

    def prepare_grouped_content(self, annotation_group: List) -> None:
        """Prepare content for grouped audio annotations"""
        from ....annotation_types.classification.classification import Text

        if (
            not isinstance(annotation_group[0].value, Text)
            or not self.enable_token_mapping
        ):
            return

        # Build token mapping for TEXT annotations
        import json

        all_content = [ann.value.answer for ann in annotation_group]
        token_mapping = {
            str(ann.frame): ann.value.answer for ann in annotation_group
        }

        content_structure = json.dumps(
            {
                "default_text": " ".join(all_content),
                "token_mapping": token_mapping,
            }
        )

        # Update the template annotation
        annotation_group[0].value = Text(answer=content_structure)
