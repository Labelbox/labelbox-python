from typing import Optional
from pydantic import BaseModel, root_validator, ValidationError


class DataRowRef(BaseModel):
    external_id: Optional[str] = None
    uid: Optional[str] = None


class FeatureSchemaRef(BaseModel):
    display_name: str
    schema_id: Optional[str] = None
    alternative_name: Optional[str] = None  # Maybe an id for this feature.

    # TODO: Validator for alternative_name to be equal to display name if not set
