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

    source: Optional[Union[ObjectAnnotation, ClassificationAnnotation]] = None
    source_ontology_name: Optional[str] = None
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

    @model_validator(mode="after")
    def validate_source_fields(self):
        if self.source is None and self.source_ontology_name is None:
            raise ValueError(
                "Either source or source_ontology_name must be provided"
            )
        return self

    @model_validator(mode="after")
    def validate_source_consistency(self):
        if self.source is not None and self.source_ontology_name is not None:
            raise ValueError(
                "Only one of 'source' or 'source_ontology_name' may be provided"
            )
        return self


class RelationshipAnnotation(BaseAnnotation):
    value: Relationship
