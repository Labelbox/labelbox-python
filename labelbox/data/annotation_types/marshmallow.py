
import dataclasses
from typing import NewType
from uuid import uuid4
import marshmallow

no_default = object()
required = lambda: dataclasses.field(default=no_default, metadata=dict(required=False))
default_none = lambda: dataclasses.field(default=None, metadata=dict(required=False))
default_uuid = lambda: dataclasses.field(default=uuid4(), metadata=dict(required=False))
default_empty = lambda: dataclasses.field(
    default_factory=list, metadata=dict(required=False)
)

Uuid = NewType("Uuid", str, field=marshmallow.fields.UUID)

@dataclasses.dataclass
class RequiredFieldMixin:
    def __post_init__(self):
        for key, value in self.__dict__.items():
            if value is no_default:
                raise TypeError(f"__init__ missing 1 required argument: '{key}'")
