from typing import Optional
from pydantic import BaseModel, root_validator, ValidationError


class DataRowRef(BaseModel):
    external_id: Optional[str] = None
    uid: Optional[str] = None


class FeatureSchemaRef(BaseModel):
    display_name: Optional[str] = None
    schema_id: Optional[str] = None

    @root_validator
    def must_provide_one(cls, values):
        if not any([values.get('display_name'), values.get('schema_id')]):
            raise ValidationError(
                "One of `file_path`, `im_bytes`, or `url` required.")
        return values
