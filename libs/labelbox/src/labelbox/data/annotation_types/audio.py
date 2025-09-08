from typing import Optional

from labelbox.data.annotation_types.annotation import ClassificationAnnotation, ObjectAnnotation
from labelbox.data.mixins import ConfidenceNotSupportedMixin, CustomMetricsNotSupportedMixin


class AudioClassificationAnnotation(ClassificationAnnotation):
    """Audio classification for specific time range
    
    Examples:
    - Speaker identification from 2500ms to 4100ms
    - Audio quality assessment for a segment
    - Language detection for audio segments
    
    Args:
        name (Optional[str]): Name of the classification
        feature_schema_id (Optional[Cuid]): Feature schema identifier
        value (Union[Text, Checklist, Radio]): Classification value
        frame (int): The frame index in milliseconds (e.g., 2500 = 2.5 seconds)
        segment_index (Optional[int]): Index of audio segment this annotation belongs to
        extra (Dict[str, Any]): Additional metadata
    """

    frame: int
    segment_index: Optional[int] = None
    
    @classmethod
    def from_time_range(cls, start_ms: int, end_ms: int, **kwargs):
        """Create from milliseconds (user-friendly) to frames (internal)
        
        Args:
            start_ms (int): Start time in milliseconds
            end_ms (int): End time in milliseconds  
            **kwargs: Additional arguments for the annotation
            
        Returns:
            AudioClassificationAnnotation: Annotation with frame set to start_ms
            
        Example:
            >>> AudioClassificationAnnotation.from_time_range(
            ...     start_ms=2500, end_ms=4100,
            ...     name="speaker_id",
            ...     value=lb_types.Radio(answer=lb_types.ClassificationAnswer(name="john"))
            ... )
        """
        return cls(frame=start_ms, **kwargs)
    
    @property
    def start_time(self) -> float:
        """Convert frame to seconds for user-facing APIs
        
        Returns:
            float: Time in seconds (e.g., 2500 -> 2.5)
        """
        return self.frame / 1000.0


class AudioObjectAnnotation(ObjectAnnotation, ConfidenceNotSupportedMixin, CustomMetricsNotSupportedMixin):
    """Audio object annotation for specific time range
    
    Examples:
    - Transcription: "Hello world" from 2500ms to 4100ms
    - Sound events: "Dog barking" from 10000ms to 12000ms
    - Audio segments with metadata
    
    Args:
        name (Optional[str]): Name of the annotation
        feature_schema_id (Optional[Cuid]): Feature schema identifier
        value (Union[TextEntity, Geometry]): Localization or text content
        frame (int): The frame index in milliseconds (e.g., 10000 = 10.0 seconds)
        keyframe (bool): Whether this is a keyframe annotation (default: True)
        segment_index (Optional[int]): Index of audio segment this annotation belongs to
        classifications (Optional[List[ClassificationAnnotation]]): Optional sub-classifications
        extra (Dict[str, Any]): Additional metadata
    """

    frame: int
    keyframe: bool = True
    segment_index: Optional[int] = None
    
    @classmethod
    def from_time_range(cls, start_ms: int, end_ms: int, **kwargs):
        """Create from milliseconds (user-friendly) to frames (internal)
        
        Args:
            start_ms (int): Start time in milliseconds
            end_ms (int): End time in milliseconds
            **kwargs: Additional arguments for the annotation
            
        Returns:
            AudioObjectAnnotation: Annotation with frame set to start_ms
            
        Example:
            >>> AudioObjectAnnotation.from_time_range(
            ...     start_ms=10000, end_ms=12500,
            ...     name="transcription",
            ...     value=lb_types.TextEntity(text="Hello world")
            ... )
        """
        return cls(frame=start_ms, **kwargs)
    
    @property
    def start_time(self) -> float:
        """Convert frame to seconds for user-facing APIs
        
        Returns:
            float: Time in seconds (e.g., 10000 -> 10.0)
        """
        return self.frame / 1000.0
