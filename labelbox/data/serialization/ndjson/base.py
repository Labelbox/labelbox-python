from typing import Optional
from uuid import uuid4
from pydantic import BaseModel, root_validator, validator, Field

from labelbox.utils import camel_case
from ...annotation_types.types import Cuid


class DataRow(BaseModel):
    id: str = None

    @validator('id', pre=True, always=True)
    def validate_id(cls, v):
        if v is None:
            raise ValueError(
                "Data row ids are not set. Use `LabelGenerator.add_to_dataset`, `LabelList.add_to_dataset`, or `Label.create_data_row`. "
                "You can also manually assign the id for each `BaseData` object"
            )
        return v


class NDJsonBase(BaseModel):
    uuid: str = None
    data_row: DataRow

    @validator('uuid', pre=True, always=True)
    def set_id(cls, v):
        return v or str(uuid4())

    class Config:
        allow_population_by_field_name = True
        alias_generator = camel_case


class NDAnnotation(NDJsonBase):
    name: Optional[str] = None
    schema_id: Optional[Cuid] = None

    @root_validator()
    def must_set_one(cls, values):
        if ('schema_id' not in values or
                values['schema_id'] is None) and ('name' not in values or
                                                  values['name'] is None):
            raise ValueError("Schema id or name are not set. Set either one.")
        return values

    def dict(self, *args, **kwargs):
        res = super().dict(*args, **kwargs)
        if 'name' in res and res['name'] is None:
            res.pop('name')
        if 'schemaId' in res and res['schemaId'] is None:
            res.pop('schemaId')
        return res