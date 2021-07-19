from typing import Any, Dict, List, Union, ForwardRef
from pydantic.class_validators import validator

from pydantic.main import BaseModel

from labelbox.data.annotation_types.reference import FeatureSchemaRef



class ClassificationAnswer(FeatureSchemaRef):
    extra: Dict[str, Any] = {}


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
