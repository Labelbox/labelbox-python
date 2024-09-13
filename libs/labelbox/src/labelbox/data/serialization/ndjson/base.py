from typing import Optional
from uuid import uuid4

from labelbox.utils import _CamelCaseMixin, is_exactly_one_set
from pydantic import model_validator, ConfigDict, BaseModel, Field
from uuid import uuid4
import threading

from ....annotated_types import Cuid

subclass_registry = {}


class _SubclassRegistryBase(BaseModel):
    model_config = ConfigDict(extra="allow")

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.__name__ != "NDAnnotation":
            with threading.Lock():
                subclass_registry[cls.__name__] = cls


class DataRow(_CamelCaseMixin):
    id: Optional[str] = None
    global_key: Optional[str] = None

    @model_validator(mode="after")
    def must_set_one(self):
        if not is_exactly_one_set(self.id, self.global_key):
            raise ValueError("Must set either id or global_key")
        return self


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
    def must_set_one(self):
        if (not hasattr(self, "schema_id") or self.schema_id is None) and (
            not hasattr(self, "name") or self.name is None
        ):
            raise ValueError("Schema id or name are not set. Set either one.")
        return self
