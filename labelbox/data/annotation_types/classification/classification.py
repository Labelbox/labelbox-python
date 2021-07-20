from typing import Any, Dict, List

from pydantic.main import BaseModel

from ..feature import FeatureSchemaRef


class ClassificationAnswer(FeatureSchemaRef):
    extra: Dict[str, Any] = {}


class Radio(BaseModel):
    answer: ClassificationAnswer


class Checklist(BaseModel):
    answer: List[ClassificationAnswer]


class Text(BaseModel):
    answer: str


class Dropdown(BaseModel):
    answer: List[ClassificationAnswer]
