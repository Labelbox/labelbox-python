from typing import Generic, TypeVar
from typing_extensions import Annotated

from pydantic import Field
from pydantic.fields import ModelField
import numpy as np

Cuid = Annotated[str, Field(min_length=25, max_length=25)]

DType = TypeVar('DType')


class TypedArray(np.ndarray, Generic[DType]):

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, val, field: ModelField):
        if not isinstance(val, np.ndarray):
            raise TypeError(f"Expected numpy array. Found {type(val)}")
        dtype_field = field.sub_fields[0]
        actual_dtype = dtype_field.type_.__args__[0]
        if val.dtype != actual_dtype:
            raise TypeError(
                f"Expected numpy array have type {actual_dtype}. Found {val.dtype}"
            )
        return val
