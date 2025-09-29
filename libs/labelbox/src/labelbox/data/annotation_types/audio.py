from typing import Optional
from pydantic import Field, AliasChoices

from labelbox.data.annotation_types.annotation import (
    ClassificationAnnotation,
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

    start_frame: int = Field(
        validation_alias=AliasChoices("start_frame", "frame"),
        serialization_alias="start_frame",
    )
    end_frame: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("end_frame", "endFrame"),
        serialization_alias="end_frame",
    )
    segment_index: Optional[int] = None

