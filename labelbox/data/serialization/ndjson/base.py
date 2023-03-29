from typing import Optional
from uuid import uuid4
from pydantic import root_validator, validator

from labelbox.utils import _CamelCaseMixin, is_exactly_one_set
from ...annotation_types.types import Cuid


class DataRow(_CamelCaseMixin):
    id: str = None
    global_key: str = None

    @root_validator()
    def must_set_one(cls, values):
        if not is_exactly_one_set(values.get('id'), values.get('global_key')):
            raise ValueError("Must set either id or global_key")
        return values


class NDJsonBase(_CamelCaseMixin):
    uuid: str = None
    data_row: DataRow

    @validator('uuid', pre=True, always=True)
    def set_id(cls, v):
        return v or str(uuid4())

    def dict(self, *args, **kwargs):
        """ Pop missing id or missing globalKey from dataRow """
        res = super().dict(*args, **kwargs)
        if not self.data_row.id:
            res['dataRow'].pop('id')
        if not self.data_row.global_key:
            res['dataRow'].pop('globalKey')
        return res


class NDAnnotation(NDJsonBase):
    name: Optional[str] = None
    schema_id: Optional[Cuid] = None
    message_id: Optional[str] = None
    page: Optional[int] = None
    unit: Optional[str] = None

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
