from labelbox import pydantic_compat
from enum import Enum
from labelbox.data.annotation_types.annotation import BaseAnnotation, ObjectAnnotation


class Relationship(pydantic_compat.BaseModel):

    class Type(Enum):
        UNIDIRECTIONAL = "unidirectional"
        BIDIRECTIONAL = "bidirectional"

    source: ObjectAnnotation
    target: ObjectAnnotation
    type: Type = Type.UNIDIRECTIONAL


class RelationshipAnnotation(BaseAnnotation):
    value: Relationship
