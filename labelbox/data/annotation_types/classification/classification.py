from typing import Any, Dict, List, Union, Optional
import warnings
from labelbox.data.annotation_types.base_annotation import BaseAnnotation

from labelbox.data.mixins import ConfidenceMixin, CustomMetricsMixin

try:
    from typing import Literal
except:
    from typing_extensions import Literal

from labelbox import pydantic_compat
from ..feature import FeatureSchema


# TODO: Replace when pydantic adds support for unions that don't coerce types
class _TempName(ConfidenceMixin, pydantic_compat.BaseModel):
    name: str

    def dict(self, *args, **kwargs):
        res = super().dict(*args, **kwargs)
        res.pop('name')
        return res


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
    classifications: List['ClassificationAnnotation'] = []

    def dict(self, *args, **kwargs) -> Dict[str, str]:
        res = super().dict(*args, **kwargs)
        if res['keyframe'] is None:
            res.pop('keyframe')
        if res['classifications'] == []:
            res.pop('classifications')
        return res


class Radio(ConfidenceMixin, CustomMetricsMixin, pydantic_compat.BaseModel):
    """ A classification with only one selected option allowed

    >>> Radio(answer = ClassificationAnswer(name = "dog"))

    """
    answer: ClassificationAnswer


class Checklist(_TempName):
    """ A classification with many selected options allowed

    >>> Checklist(answer = [ClassificationAnswer(name = "cloudy")])

    """
    name: Literal["checklist"] = "checklist"
    answer: List[ClassificationAnswer]


class Text(ConfidenceMixin, CustomMetricsMixin, pydantic_compat.BaseModel):
    """ Free form text

    >>> Text(answer = "some text answer")

    """
    answer: str


class Dropdown(_TempName):
    """
    - A classification with many selected options allowed .
    - This is not currently compatible with MAL.

    Deprecation Notice: Dropdown classification is deprecated and will be
        removed in a future release. Dropdown will also
        no longer be able to be created in the Editor on 3/31/2022.    
    """
    name: Literal["dropdown"] = "dropdown"
    answer: List[ClassificationAnswer]

    def __init__(self, **data: Any):
        super().__init__(**data)
        warnings.warn("Dropdown classification is deprecated and will be "
                      "removed in a future release")


class ClassificationAnnotation(BaseAnnotation, ConfidenceMixin,
                               CustomMetricsMixin):
    """Classification annotations (non localized)

    >>> ClassificationAnnotation(
    >>>     value=Text(answer="my caption message"),
    >>>     feature_schema_id="my-feature-schema-id"
    >>> )

    Args:
        name (Optional[str])
        classifications (Optional[List[ClassificationAnnotation]]): Optional sub classification of the annotation
        feature_schema_id (Optional[Cuid])
        value (Union[Text, Checklist, Radio, Dropdown])
        extra (Dict[str, Any])
     """

    value: Union[Text, Checklist, Radio, Dropdown]
    message_id: Optional[str] = None


ClassificationAnswer.update_forward_refs()
