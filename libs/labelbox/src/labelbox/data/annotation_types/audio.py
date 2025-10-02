from typing import Optional, List
from pydantic import Field, AliasChoices

from labelbox.data.annotation_types.annotation import (
    ClassificationAnnotation,
)
from labelbox.data.annotation_types.classification.classification import FrameLocation


class AudioClassificationAnnotation(ClassificationAnnotation):
    """Audio classification for specific time range(s)

    Examples:
    - Speaker identification from 2500ms to 4100ms
    - Audio quality assessment for a segment
    - Language detection for audio segments

    Args:
        name (Optional[str]): Name of the classification
        feature_schema_id (Optional[Cuid]): Feature schema identifier
        value (Union[Text, Checklist, Radio]): Classification value
        frames (Optional[List[FrameLocation]]): List of frame ranges (in milliseconds)
        segment_index (Optional[int]): Index of audio segment this annotation belongs to
        extra (Dict[str, Any]): Additional metadata
    """

    frames: Optional[List[FrameLocation]] = None
    segment_index: Optional[int] = None
