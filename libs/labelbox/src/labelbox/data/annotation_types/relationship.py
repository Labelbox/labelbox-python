from pydantic import BaseModel
from enum import Enum
from labelbox.data.annotation_types.annotation import (
    BaseAnnotation,
    ObjectAnnotation,
)


class Relationship(BaseModel):
    class Type(Enum):
        UNIDIRECTIONAL = "unidirectional"
        BIDIRECTIONAL = "bidirectional"

    source: ObjectAnnotation
    target: ObjectAnnotation
    type: Type = Type.UNIDIRECTIONAL


class RelationshipAnnotation(BaseAnnotation):
    value: Relationship
