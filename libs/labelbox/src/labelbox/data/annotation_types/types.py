import sys
from typing import Generic, TypeVar, Any, Type

from labelbox.typing_imports import Annotated
from packaging import version
import numpy as np

from pydantic import Field, GetCoreSchemaHandler, TypeAdapter
from pydantic_core import core_schema

Cuid = Annotated[str, Field(min_length=25, max_length=25)]

DType = TypeVar('DType')
DShape = TypeVar('DShape')


class _TypedArray(np.ndarray, Generic[DType, DShape]):

    # @classmethod
    # def __get_validators__(cls):
    #     yield cls.validate

    @classmethod
    def __get_pydantic_core_schema__(
            cls, source_type: Type[Any],
            handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:

        # assert source is CompressedString
        return core_schema.with_info_after_validator_function(
            function=cls.validate,
            schema=core_schema.any_schema(),
            field_name=source_type.__args__[-1].__args__[0])

    @classmethod
    def validate(cls, val, info):
        if not isinstance(val, np.ndarray):
            raise TypeError(f"Expected numpy array. Found {type(val)}")

        actual_type = info.field_name
        if str(val.dtype) != actual_type:
            raise TypeError(
                f"Expected numpy array have type {actual_dtype}. Found {val.dtype}"
            )
        return val


if version.parse(np.__version__) >= version.parse('1.25.0'):
    from typing import GenericAlias
    TypedArray = GenericAlias(_TypedArray, (Any, DType))
elif version.parse(np.__version__) >= version.parse('1.23.0'):
    from numpy._typing import _GenericAlias
    TypedArray = _GenericAlias(_TypedArray, (Any, DType))
elif version.parse('1.22.0') <= version.parse(
        np.__version__) < version.parse('1.23.0'):
    from numpy.typing import _GenericAlias
    TypedArray = _GenericAlias(_TypedArray, (Any, DType))
else:
    TypedArray = _TypedArray[Any, DType]
