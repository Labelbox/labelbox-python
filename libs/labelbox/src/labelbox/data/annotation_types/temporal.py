"""
Temporal classification annotations for audio, video, and other time-based media.

These classes provide a unified, recursive structure for temporal annotations with
frame-level precision. All temporal classifications support nested hierarchies.
"""

from typing import List, Optional, Tuple, Union
from pydantic import Field

from labelbox.data.annotation_types.annotation import ClassificationAnnotation
from labelbox.data.annotation_types.classification.classification import (
    ClassificationAnswer,
    FrameLocation,
)


class TemporalClassificationAnswer(ClassificationAnswer):
    """
    Temporal answer for Radio/Checklist questions with frame ranges.

    Represents a single answer option that can exist at multiple discontinuous
    time ranges and contain nested classifications.

    Args:
        name (str): Name of the answer option
        frames (List[Tuple[int, int]]): List of (start_frame, end_frame) ranges in milliseconds
        classifications (Optional[List[Union[TemporalClassificationText, TemporalClassificationQuestion]]]):
            Nested classifications within this answer
        feature_schema_id (Optional[str]): Feature schema identifier
        extra (dict): Additional metadata

    Example:
        >>> # Radio answer with nested classifications
        >>> answer = TemporalClassificationAnswer(
        >>>     name="user",
        >>>     frames=[(200, 1600)],
        >>>     classifications=[
        >>>         TemporalClassificationQuestion(
        >>>             name="tone",
        >>>             answers=[
        >>>                 TemporalClassificationAnswer(
        >>>                     name="professional",
        >>>                     frames=[(1000, 1600)]
        >>>                 )
        >>>             ]
        >>>         )
        >>>     ]
        >>> )
    """

    frames: List[Tuple[int, int]] = Field(
        default_factory=list,
        description="List of (start_frame, end_frame) tuples in milliseconds",
    )
    classifications: Optional[
        List[Union["TemporalClassificationText", "TemporalClassificationQuestion"]]
    ] = None


class TemporalClassificationText(ClassificationAnnotation):
    """
    Temporal text classification with multiple text values at different frame ranges.

    Allows multiple text annotations at different time segments, each with precise
    frame ranges. Supports recursive nesting of text and question classifications.

    Args:
        name (str): Name of the text classification
        values (List[Tuple[int, int, str]]): List of (start_frame, end_frame, text_value) tuples
        classifications (Optional[List[Union[TemporalClassificationText, TemporalClassificationQuestion]]]):
            Nested classifications
        feature_schema_id (Optional[str]): Feature schema identifier
        extra (dict): Additional metadata

    Example:
        >>> # Simple text with multiple temporal values
        >>> transcription = TemporalClassificationText(
        >>>     name="transcription",
        >>>     values=[
        >>>         (1600, 2000, "Hello, how can I help you?"),
        >>>         (2500, 3000, "Thank you for calling!"),
        >>>     ]
        >>> )
        >>>
        >>> # Text with nested classifications
        >>> transcription_with_notes = TemporalClassificationText(
        >>>     name="transcription",
        >>>     values=[
        >>>         (1600, 2000, "Hello, how can I help you?"),
        >>>     ],
        >>>     classifications=[
        >>>         TemporalClassificationText(
        >>>             name="speaker_notes",
        >>>             values=[
        >>>                 (1600, 2000, "Polite greeting"),
        >>>             ]
        >>>         )
        >>>     ]
        >>> )
    """

    # Override parent's value field
    value: List[Tuple[int, int, str]] = Field(
        default_factory=list,
        description="List of (start_frame, end_frame, text_value) tuples",
    )
    classifications: Optional[
        List[Union["TemporalClassificationText", "TemporalClassificationQuestion"]]
    ] = None


class TemporalClassificationQuestion(ClassificationAnnotation):
    """
    Temporal Radio/Checklist question with multiple answer options.

    Represents a question with one or more answer options, each having their own
    frame ranges. Radio questions have a single answer, Checklist can have multiple.

    Args:
        name (str): Name of the question/classification
        answers (List[TemporalClassificationAnswer]): List of answer options with frame ranges
        feature_schema_id (Optional[str]): Feature schema identifier
        extra (dict): Additional metadata

    Note:
        - Radio: Single answer in the answers list
        - Checklist: Multiple answers in the answers list
        The serializer automatically handles the distinction based on the number of answers.

    Example:
        >>> # Radio question (single answer)
        >>> speaker = TemporalClassificationQuestion(
        >>>     name="speaker",
        >>>     answers=[
        >>>         TemporalClassificationAnswer(
        >>>             name="user",
        >>>             frames=[(200, 1600)]
        >>>         )
        >>>     ]
        >>> )
        >>>
        >>> # Checklist question (multiple answers)
        >>> audio_quality = TemporalClassificationQuestion(
        >>>     name="audio_quality",
        >>>     answers=[
        >>>         TemporalClassificationAnswer(
        >>>             name="background_noise",
        >>>             frames=[(0, 1500), (2000, 3000)]
        >>>         ),
        >>>         TemporalClassificationAnswer(
        >>>             name="echo",
        >>>             frames=[(2200, 2900)]
        >>>         )
        >>>     ]
        >>> )
        >>>
        >>> # Nested structure: Radio > Radio > Radio
        >>> speaker_with_tone = TemporalClassificationQuestion(
        >>>     name="speaker",
        >>>     answers=[
        >>>         TemporalClassificationAnswer(
        >>>             name="user",
        >>>             frames=[(200, 1600)],
        >>>             classifications=[
        >>>                 TemporalClassificationQuestion(
        >>>                     name="tone",
        >>>                     answers=[
        >>>                         TemporalClassificationAnswer(
        >>>                             name="professional",
        >>>                             frames=[(1000, 1600)]
        >>>                         )
        >>>                     ]
        >>>                 )
        >>>             ]
        >>>         )
        >>>     ]
        >>> )
    """

    # Override parent's value field
    value: List[TemporalClassificationAnswer] = Field(
        default_factory=list,
        description="List of temporal answer options",
    )
    classifications: Optional[
        List[Union["TemporalClassificationText", "TemporalClassificationQuestion"]]
    ] = None


# Update forward references for recursive types
TemporalClassificationAnswer.model_rebuild()
TemporalClassificationText.model_rebuild()
TemporalClassificationQuestion.model_rebuild()
