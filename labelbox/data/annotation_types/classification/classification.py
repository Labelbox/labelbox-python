from typing import Any, List, Union, ForwardRef

from pydantic.main import BaseModel

from labelbox.data.annotation_types.reference import FeatureSchemaRef

# Requires 3.7+
Subclass = ForwardRef('Subclass')

class ClassificationAnswer(FeatureSchemaRef):
    ...


class Radio(BaseModel):
    answer: ClassificationAnswer


class CheckList(BaseModel):
    answer: List[ClassificationAnswer]


class Text(BaseModel):
    answer: str


class Dropdown(BaseModel):
    answer: List[ClassificationAnswer]

class Classification:
    value: Union[Dropdown, Text, CheckList, Radio]

class Subclass(Classification, FeatureSchemaRef):
    classifications: List["Subclass"] = []
# To support recursive subclasses
Subclass.update_forward_refs()
