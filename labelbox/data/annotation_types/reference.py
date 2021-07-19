from typing import Optional
from pydantic import BaseModel


class DataRowRef(BaseModel):
    external_id: Optional[str] = None
    uid: Optional[str] = None


class FeatureSchemaRef(BaseModel):
    display_name: Optional[str] = None
    schema_id: Optional[str] = None

    # TODO: Validate that one of these is set..


