from typing import Any, Dict, List, Union, Optional
from labelbox.data.annotation_types.base_annotation import BaseAnnotation

from labelbox.data.mixins import ConfidenceMixin, CustomMetricsMixin

from pydantic import BaseModel
from ..feature import FeatureSchema


class FrameLocation(BaseModel):
    """Represents a temporal frame range with start and end times (in milliseconds)."""
    start: int
    end: int


class ClassificationAnswer(FeatureSchema, ConfidenceMixin, CustomMetricsMixin):
    """
    - Represents a classification option.
    - Because it inherits from FeatureSchema
        the option can be represented with either the name or feature_schema_id

    - The keyframe arg only applies to video classifications.
      Each answer can have a keyframe independent of the others.
        So unlike object annotations, classification annotations
          track keyframes at a classification answer level.

    - For temporal classifications (audio/video), optional frames can specify
      one or more time ranges for this answer. Must be within root annotation's frame ranges.
      Defaults to root frame ranges if not specified.
    """

    extra: Dict[str, Any] = {}
    keyframe: Optional[bool] = None
    classifications: Optional[List["ClassificationAnnotation"]] = None
    frames: Optional[List[FrameLocation]] = None

    # Deprecated: use frames instead
    start_frame: Optional[int] = None
    end_frame: Optional[int] = None


class Radio(ConfidenceMixin, CustomMetricsMixin, BaseModel):
    """A classification with only one selected option allowed

    >>> Radio(answer = ClassificationAnswer(name = "dog"))

    """

    answer: ClassificationAnswer


class Checklist(ConfidenceMixin, BaseModel):
    """A classification with many selected options allowed

    >>> Checklist(answer = [ClassificationAnswer(name = "cloudy")])

    """

    answer: List[ClassificationAnswer]


class Text(ConfidenceMixin, CustomMetricsMixin, BaseModel):
    """Free form text

    >>> Text(answer = "some text answer")

    """

    answer: str


class ClassificationAnnotation(
    BaseAnnotation, ConfidenceMixin, CustomMetricsMixin
):
    """Classification annotations (non localized)

    >>> ClassificationAnnotation(
    >>>     value=Text(answer="my caption message"),
    >>>     feature_schema_id="my-feature-schema-id"
    >>> )

    Args:
        name (Optional[str])
        classifications (Optional[List[ClassificationAnnotation]]): Optional sub classification of the annotation
        feature_schema_id (Optional[Cuid])
        value (Union[Text, Checklist, Radio])
        frames (Optional[List[FrameLocation]]): Frame ranges for temporal classifications (audio/video). Must be within root annotation's frame ranges. Defaults to root frames if not specified.
        extra (Dict[str, Any])
    """

    value: Union[Text, Checklist, Radio]
    message_id: Optional[str] = None
    frames: Optional[List[FrameLocation]] = None

    # Deprecated: use frames instead
    start_frame: Optional[int] = None
    end_frame: Optional[int] = None
