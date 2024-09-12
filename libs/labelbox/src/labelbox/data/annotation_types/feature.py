from typing import Optional
from pydantic import BaseModel, model_validator, model_serializer

from ...annotated_types import Cuid


class FeatureSchema(BaseModel):
    """
    Class that represents a feature schema.
    Could be a annotation, a subclass, or an option.
    Schema ids might not be known when constructing these objects so both a name and schema id are valid.
    """

    name: Optional[str] = None
    feature_schema_id: Optional[Cuid] = None

    @model_validator(mode="after")
    def must_set_one(self):
        if self.feature_schema_id is None and self.name is None:
            raise ValueError(
                "Must set either feature_schema_id or name for all feature schemas"
            )
        return self
