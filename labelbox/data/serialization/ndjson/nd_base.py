from uuid import uuid4
from pydantic import validator
from labelbox.data.serialization.ndjson.data_row import DataRow

from labelbox.utils import _CamelCaseMixin


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
