from typing import Optional, List
from pydantic import Field, AliasChoices

from labelbox.data.annotation_types.annotation import (
    ClassificationAnnotation,
)
from labelbox.data.annotation_types.classification.classification import FrameLocation


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
        start_frame (Optional[int]): Start frame in milliseconds
        end_frame (Optional[int]): End frame in milliseconds
        segment_index (Optional[int]): Index of audio segment this annotation belongs to
        extra (Dict[str, Any]): Additional metadata

    Note:
        Parent AudioClassificationAnnotation uses start_frame/end_frame (single range).
        Nested classifications/answers use frames: List[FrameLocation] for discontinuous ranges.
        Multiple time ranges for same classification = multiple separate annotation objects.
    """

    start_frame: Optional[int] = Field(
        default=None, validation_alias=AliasChoices("start_frame", "frame")
    )
    end_frame: Optional[int] = None
    segment_index: Optional[int] = None
