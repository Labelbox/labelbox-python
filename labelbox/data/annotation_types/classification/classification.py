from typing import Any, Dict, List, Union, ForwardRef
from pydantic.class_validators import validator

from pydantic.main import BaseModel

from labelbox.data.annotation_types.reference import FeatureSchemaRef

# Requires 3.7+
Subclass = ForwardRef('Subclass')


class ClassificationAnswer(FeatureSchemaRef):
    extra: Dict[str, Any]


class Radio(BaseModel):
    answer: ClassificationAnswer


class CheckList(BaseModel):
    answer: List[ClassificationAnswer]
    # TODO: Validate that there is only one of each answer


class Text(BaseModel):
    answer: str


class Dropdown(BaseModel):
    answer: List[ClassificationAnswer]
    # TODO: Validate that there is only one of each answer


class Classification(BaseModel):
    value: Union[Dropdown, Text, CheckList, Radio]
    extra: Dict[str, Any] = {}


class Subclass(Classification, FeatureSchemaRef):
    classifications: List["Subclass"] = []


# To support recursive subclasses
Subclass.update_forward_refs()
