from typing import Optional

from ...annotation_types.types import Cuid
from pydantic import BaseModel, ConfigDict, model_validator, model_serializer
from pydantic.alias_generators import to_camel


class LBV1Feature(BaseModel):
    keyframe: Optional[bool] = None
    title: str = None
    value: Optional[str] = None
    schema_id: Optional[Cuid] = None
    feature_id: Optional[Cuid] = None
    model_config = ConfigDict(populate_by_name = True, alias_generator = to_camel)

    @model_validator(mode = "after")
    def check_ids(self, values):
        if self.value is None:
            self.value = self.title
        return self

    @model_serializer(mode = "wrap")
    def serialize_model(self, handler):
        res = handler(self)
        # This means these are no video frames ..
        if self.keyframe is None:
            res.pop('keyframe')
        return res
