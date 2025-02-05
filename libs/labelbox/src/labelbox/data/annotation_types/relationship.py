from typing import Union, Optional
from pydantic import BaseModel
from enum import Enum
from labelbox.data.annotation_types.annotation import (
    BaseAnnotation,
    ObjectAnnotation,
    ClassificationAnnotation,
)


class Relationship(BaseModel):
    class Type(Enum):
        UNIDIRECTIONAL = "unidirectional"
        BIDIRECTIONAL = "bidirectional"

    source: Union[ObjectAnnotation, ClassificationAnnotation]
    target: ObjectAnnotation
    type: Type = Type.UNIDIRECTIONAL
    readonly: Optional[bool] = None


class RelationshipAnnotation(BaseAnnotation):
    value: Relationship
