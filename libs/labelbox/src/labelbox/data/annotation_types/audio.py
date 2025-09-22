from typing import Optional

from labelbox.data.annotation_types.annotation import (
    ClassificationAnnotation,
    ObjectAnnotation,
)
from labelbox.data.mixins import (
    ConfidenceNotSupportedMixin,
    CustomMetricsNotSupportedMixin,
)


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
        start_frame (int): The frame index in milliseconds (e.g., 2500 = 2.5 seconds)
        end_frame (Optional[int]): End frame in milliseconds (for time ranges)
        segment_index (Optional[int]): Index of audio segment this annotation belongs to
        extra (Dict[str, Any]): Additional metadata
    """

    start_frame: int
    end_frame: Optional[int] = None
    segment_index: Optional[int] = None


class AudioObjectAnnotation(
    ObjectAnnotation,
    ConfidenceNotSupportedMixin,
    CustomMetricsNotSupportedMixin,
):
    """Audio object annotation for specific time range

    Examples:
    - Transcription: "Hello world" from 2500ms to 4100ms
    - Sound events: "Dog barking" from 10000ms to 12000ms
    - Audio segments with metadata

    Args:
        name (Optional[str]): Name of the annotation
        feature_schema_id (Optional[Cuid]): Feature schema identifier
        value (Union[TextEntity, Geometry]): Localization or text content
        start_frame (int): The frame index in milliseconds (e.g., 10000 = 10.0 seconds)
        end_frame (Optional[int]): End frame in milliseconds (for time ranges)
        keyframe (bool): Whether this is a keyframe annotation (default: True)
        segment_index (Optional[int]): Index of audio segment this annotation belongs to
        classifications (Optional[List[ClassificationAnnotation]]): Optional sub-classifications
        extra (Dict[str, Any]): Additional metadata
    """

    start_frame: int
    end_frame: Optional[int] = None
    keyframe: bool = True
    segment_index: Optional[int] = None
