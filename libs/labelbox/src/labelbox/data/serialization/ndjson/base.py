from typing import Optional
from uuid import uuid4

from labelbox.utils import _CamelCaseMixin, is_exactly_one_set
from ...annotation_types.types import Cuid
from pydantic import field_validator, model_validator, model_serializer, ConfigDict, BaseModel, Field
from uuid import UUID, uuid4

subclass_registry = {}

class SubclassRegistryBase(BaseModel):
    
    model_config = ConfigDict(extra="allow")
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.__name__ != "NDAnnotation":
            subclass_registry[cls.__name__] = cls  

class DataRow(_CamelCaseMixin):
    id: Optional[str] = None
    global_key: Optional[str] = None
    

    @model_validator(mode="after")
    def must_set_one(cls):
        if not is_exactly_one_set(cls.id, cls.global_key):
            raise ValueError("Must set either id or global_key")
        return cls


class NDJsonBase(_CamelCaseMixin):
    uuid: Optional[str] = Field(default_factory=lambda: str(uuid4()))
    data_row: DataRow


class NDAnnotation(NDJsonBase):
    name: Optional[str] = None
    schema_id: Optional[Cuid] = None
    message_id: Optional[str] = None
    page: Optional[int] = None
    unit: Optional[str] = None

    @model_validator(mode="after")
    def must_set_one(cls):
        if (not hasattr(cls, "schema_id") or cls.schema_id is None) and (not hasattr(cls, "name") or cls.name is None):
            raise ValueError("Schema id or name are not set. Set either one.")
        return cls
