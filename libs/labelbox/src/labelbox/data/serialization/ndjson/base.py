from typing import Optional
from uuid import uuid4

from labelbox.utils import _CamelCaseMixin, is_exactly_one_set
from pydantic import model_validator, field_validator
from ...annotation_types.types import Cuid


class DataRow(_CamelCaseMixin):
    id: Optional[str] = None
    global_key: Optional[str] = None

    @model_validator(mode='after')
    def must_set_one(self):
        if self.id is None and self.global_key is None:
            raise ValueError(
                "Must set either id or global_key for all data rows")

        return self


class NDJsonBase(_CamelCaseMixin):
    uuid: str
    data_row: DataRow

    @model_validator(mode='before')
    @classmethod
    def set_uuid(cls, data):
        if data.get('uuid') is None:
            data['uuid'] = str(uuid4())
        return data

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

    @model_validator(mode='after')
    def must_set_one(self):
        if self.schema_id is None and self.name is None:
            raise ValueError("Schema id or name are not set. Set either one.")
        if self.schema_id is not None and self.name is not None:
            raise ValueError("Schema id and name are both set. Set only one.")
        return self

    def dict(self, *args, **kwargs):
        res = super().dict(*args, **kwargs)
        if 'name' in res and res['name'] is None:
            res.pop('name')
        if 'schemaId' in res and res['schemaId'] is None:
            res.pop('schemaId')
        return res
