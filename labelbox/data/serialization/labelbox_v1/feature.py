from pydantic import BaseModel, Field, root_validator
from typing import Optional




class LBV1Feature(BaseModel):
    title: str = None
    value: Optional[str] = None
    schema_id: str = Field(None, alias='schemaId')
    feature_id: Optional[str] = Field(None, alias='featureId')

    # TODO: Validator that sets value == title if not set.
    @root_validator
    def check_ids(cls, values):
        if values.get('value') is None:
            values['value'] = values['title']
        return values


    class Config:
        allow_population_by_field_name = True
