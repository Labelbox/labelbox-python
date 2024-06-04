from typing import Optional

from pydantic import BaseModel, model_validator

from .types import Cuid


class FeatureSchema(BaseModel):
    """
    Class that represents a feature schema.
    Could be a annotation, a subclass, or an option.
    Schema ids might not be known when constructing these objects so both a name and schema id are valid.
    """
    name: Optional[str] = None
    feature_schema_id: Optional[Cuid] = None

    @model_validator(mode='before')
    @classmethod
    def must_set_one(cls, values):
        if values['feature_schema_id'] is None and values['name'] is None:
            raise ValueError(
                "Must set either feature_schema_id or name for all feature schemas"
            )
        return values

    def dict(self, *args, **kwargs):
        res = super().dict(*args, **kwargs)
        if 'name' in res and res['name'] is None:
            res.pop('name')
        if 'featureSchemaId' in res and res['featureSchemaId'] is None:
            res.pop('featureSchemaId')
        return res
