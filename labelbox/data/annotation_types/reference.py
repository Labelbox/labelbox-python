from typing import Optional
from pydantic import BaseModel, root_validator, ValidationError


class DataRowRef(BaseModel):
    external_id: Optional[str] = None
    uid: Optional[str] = None


class FeatureSchemaRef(BaseModel):
    display_name: str
    schema_id: Optional[str] = None
