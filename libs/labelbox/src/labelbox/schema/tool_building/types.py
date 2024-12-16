from typing import Annotated, List
from pydantic import Field, BaseModel
from typing import TypedDict


class FeatureSchemaAttribute(TypedDict):
    attributeName: str
    attributeValue: str

FeatureSchemaAttriubte = Annotated[FeatureSchemaAttribute, Field()]

FeatureSchemaId = Annotated[str, Field(min_length=25, max_length=25)]
SchemaId = Annotated[str, Field(min_length=25, max_length=25)]
FeatureSchemaAttributes = Annotated[List[FeatureSchemaAttribute], Field(default_factory=list)]
