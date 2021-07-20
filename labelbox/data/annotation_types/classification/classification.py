from typing import Any, Dict, List

from labelbox.data.annotation_types.reference import FeatureSchemaRef
from pydantic.main import BaseModel


class ClassificationAnswer(FeatureSchemaRef):
    extra: Dict[str, Any] = {}


class Radio(BaseModel):
    answer: ClassificationAnswer


class CheckList(BaseModel):
    answer: List[ClassificationAnswer]


class Text(BaseModel):
    answer: str


class Dropdown(BaseModel):
    answer: List[ClassificationAnswer]
