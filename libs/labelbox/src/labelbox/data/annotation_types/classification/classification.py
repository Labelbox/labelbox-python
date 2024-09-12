from typing import Any, Dict, List, Union, Optional
from labelbox.data.annotation_types.base_annotation import BaseAnnotation

from labelbox.data.mixins import ConfidenceMixin, CustomMetricsMixin

from pydantic import BaseModel
from ..feature import FeatureSchema


class ClassificationAnswer(FeatureSchema, ConfidenceMixin, CustomMetricsMixin):
    """
    - Represents a classification option.
    - Because it inherits from FeatureSchema
        the option can be represented with either the name or feature_schema_id

    - The keyframe arg only applies to video classifications.
      Each answer can have a keyframe independent of the others.
        So unlike object annotations, classification annotations
          track keyframes at a classification answer level.
    """

    extra: Dict[str, Any] = {}
    keyframe: Optional[bool] = None
    classifications: Optional[List["ClassificationAnnotation"]] = None


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
        extra (Dict[str, Any])
    """

    value: Union[Text, Checklist, Radio]
    message_id: Optional[str] = None
