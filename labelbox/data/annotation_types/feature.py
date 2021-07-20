from typing import Optional

from pydantic import BaseModel, root_validator


class FeatureSchemaRef(BaseModel):
    display_name: Optional[str] = None
    schema_id: Optional[str] = None

    @root_validator
    def must_set_one(cls, values):
        if values['schema_id'] is None and values['display_name'] is None:
            raise ValueError(
                "Must set either schema_id or display name for all feature schemas"
            )
        return values
