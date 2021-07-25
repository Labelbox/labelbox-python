from typing import Any, Dict, List

from pydantic.main import BaseModel

from ..feature import FeatureSchema


class ClassificationAnswer(FeatureSchema):
    """
    - Represents a classification option.
    - Because it inherits from FeatureSchema
        the option can be represented with either the name or schema_id
    """
    extra: Dict[str, Any] = {}


class Radio(BaseModel):
    """ A classification with only one selected option allowed """
    answer: ClassificationAnswer


class Checklist(BaseModel):
    """ A classification with many selected options allowed """
    answer: List[ClassificationAnswer]


class Text(BaseModel):
    """ Free form text """
    answer: str


class Dropdown(BaseModel):
    """
    - A classification with many selected options allowed .
    - This is not currently compatible with MAL.
    """
    answer: List[ClassificationAnswer]
