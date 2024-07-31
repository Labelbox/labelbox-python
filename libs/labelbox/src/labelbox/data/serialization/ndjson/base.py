from typing import Optional
from uuid import uuid4

from labelbox.utils import _CamelCaseMixin, is_exactly_one_set
from labelbox import pydantic_compat
from ...annotation_types.types import Cuid

subclass_registry = {}

class SubclassRegistryBase(pydantic_compat.BaseModel):

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.__name__ != "NDAnnotation":
            subclass_registry[cls.__name__] = cls 
    
    class Config:
        extra = "allow" 
            

class DataRow(_CamelCaseMixin):
    id: str = None
    global_key: str = None

    @pydantic_compat.root_validator()
    def must_set_one(cls, values):
        if not is_exactly_one_set(values.get('id'), values.get('global_key')):
            raise ValueError("Must set either id or global_key")
        return values


class NDJsonBase(_CamelCaseMixin):
    uuid: str = None
    data_row: Optional[DataRow] = None

    @pydantic_compat.validator('uuid', pre=True, always=True)
    def set_id(cls, v):
        return v or str(uuid4())

    def dict(self, *args, **kwargs):
        """ Pop missing id or missing globalKey from dataRow """
        res = super().dict(*args, **kwargs)
        if self.data_row and not self.data_row.id:
            if "data_row" in res:
                res["data_row"].pop("id")
            else:
                res['dataRow'].pop('id')
        if self.data_row and not self.data_row.global_key:
            if "data_row" in res:
                res["data_row"].pop("global_key")
            else:
                res['dataRow'].pop('globalKey')
        if not self.data_row:
            del res["dataRow"]
        return res


class NDAnnotation(NDJsonBase):
    name: Optional[str] = None
    schema_id: Optional[Cuid] = None
    message_id: Optional[str] = None
    page: Optional[int] = None
    unit: Optional[str] = None

    @pydantic_compat.root_validator()
    def must_set_one(cls, values):
        if ('schema_id' not in values or values['schema_id']
                is None) and ('name' not in values or values['name'] is None):
            raise ValueError("Schema id or name are not set. Set either one.")
        return values

    def dict(self, *args, **kwargs):
        res = super().dict(*args, **kwargs)
        if 'name' in res and res['name'] is None:
            res.pop('name')
        if 'schemaId' in res and res['schemaId'] is None:
            res.pop('schemaId')
        return res
