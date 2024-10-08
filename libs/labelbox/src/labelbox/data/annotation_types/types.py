from typing import Generic, TypeVar
import numpy as np
from pydantic_core import core_schema

DType = TypeVar("DType")
DShape = TypeVar("DShape")


class TypedArray(np.ndarray, Generic[DType, DShape]):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: type, _model: type
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_plain_validator_function(cls.validate)

    @classmethod
    def validate(cls, val):
        if not isinstance(val, np.ndarray):
            raise TypeError(f"Expected numpy array. Found {type(val)}")
        return val
