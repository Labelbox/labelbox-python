from typing import Optional

from pydantic import BaseModel, root_validator

from labelbox.utils import camel_case
from ...annotation_types.types import Cuid


class LBV1Feature(BaseModel):
    keyframe: Optional[bool] = None
    title: str = None
    value: Optional[str] = None
    schema_id: Optional[Cuid] = None
    feature_id: Optional[Cuid] = None

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
        alias_generator = camel_case
