from typing import Optional

from labelbox.data.annotation_types.annotation import ClassificationAnnotation, ObjectAnnotation
from labelbox.data.mixins import ConfidenceNotSupportedMixin, CustomMetricsNotSupportedMixin


class AudioClassificationAnnotation(ClassificationAnnotation):
    """Audio classification for specific time range
    
    Examples:
    - Speaker identification from 2.5s to 4.1s
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
    def from_time_range(cls, start_sec: float, end_sec: float, **kwargs):
        """Create from seconds (user-friendly) to frames (internal)
        
        Args:
            start_sec (float): Start time in seconds
            end_sec (float): End time in seconds  
            **kwargs: Additional arguments for the annotation
            
        Returns:
            AudioClassificationAnnotation: Annotation with frame set to start_sec * 1000
            
        Example:
            >>> AudioClassificationAnnotation.from_time_range(
            ...     start_sec=2.5, end_sec=4.1,
            ...     name="speaker_id",
            ...     value=lb_types.Radio(answer=lb_types.ClassificationAnswer(name="john"))
            ... )
        """
        return cls(frame=int(start_sec * 1000), **kwargs)
    
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
    - Transcription: "Hello world" from 2.5s to 4.1s
    - Sound events: "Dog barking" from 10s to 12s
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
    def from_time_range(cls, start_sec: float, end_sec: float, **kwargs):
        """Create from seconds (user-friendly) to frames (internal)
        
        Args:
            start_sec (float): Start time in seconds
            end_sec (float): End time in seconds
            **kwargs: Additional arguments for the annotation
            
        Returns:
            AudioObjectAnnotation: Annotation with frame set to start_sec * 1000
            
        Example:
            >>> AudioObjectAnnotation.from_time_range(
            ...     start_sec=10.0, end_sec=12.5,
            ...     name="transcription",
            ...     value=lb_types.TextEntity(text="Hello world")
            ... )
        """
        return cls(frame=int(start_sec * 1000), **kwargs)
    
    @property
    def start_time(self) -> float:
        """Convert frame to seconds for user-facing APIs
        
        Returns:
            float: Time in seconds (e.g., 10000 -> 10.0)
        """
        return self.frame / 1000.0
