from typing import Any, Dict, List

try:
    from typing import Literal
except:
    from typing_extensions import Literal

from pydantic import BaseModel, validator
from ..feature import FeatureSchema


# TODO: Replace when pydantic adds support for unions that don't coerce types
class _TempName(BaseModel):
    name: str

    def dict(self, *args, **kwargs):
        res = super().dict(*args, **kwargs)
        res.pop('name')
        return res


class ClassificationAnswer(FeatureSchema):
    """
    - Represents a classification option.
    - Because it inherits from FeatureSchema
        the option can be represented with either the name or feature_schema_id
    """
    extra: Dict[str, Any] = {}


class Radio(BaseModel):
    """ A classification with only one selected option allowed """
    answer: ClassificationAnswer


class Checklist(_TempName):
    """ A classification with many selected options allowed """
    name: Literal["checklist"] = "checklist"
    answer: List[ClassificationAnswer]


class Text(BaseModel):
    """ Free form text """
    answer: str


class Dropdown(_TempName):
    """
    - A classification with many selected options allowed .
    - This is not currently compatible with MAL.
    """
    name: Literal["dropdown"] = "dropdown"
    answer: List[ClassificationAnswer]
