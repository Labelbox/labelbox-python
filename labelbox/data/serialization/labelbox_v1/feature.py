from typing import Optional

from pydantic import BaseModel, Field, root_validator


class LBV1Feature(BaseModel):
    keyframe: Optional[bool] = Field(None)
    title: str = None
    value: Optional[str] = None
    schema_id: str = Field(None, alias='schemaId')
    feature_id: Optional[str] = Field(None, alias='featureId')

    @root_validator
    def check_ids(cls, values):
        if values.get('value') is None:
            values['value'] = values['title']
        return values

    def dict(self, *args, **kwargs):
        res = super().dict(*args, **kwargs)
        # This means these are no video frames ..
        if self.keyframe is None:
            res.pop('keyframe')
        return res

    class Config:
        allow_population_by_field_name = True
