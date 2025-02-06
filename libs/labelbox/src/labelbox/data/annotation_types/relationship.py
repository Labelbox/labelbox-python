from typing import Union, Optional
from pydantic import BaseModel, model_validator
from enum import Enum
import warnings
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

    @model_validator(mode="after")
    def check_readonly(self):
        if self.readonly is True:
            warnings.warn(
                "Creating a relationship with readonly=True is in beta and its behavior may change in future releases.",
            )
        return self


class RelationshipAnnotation(BaseAnnotation):
    value: Relationship
