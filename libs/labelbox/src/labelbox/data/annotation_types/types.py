import sys
from typing import Generic, TypeVar, Any

from labelbox.typing_imports import Annotated
from packaging import version
import numpy as np

from pydantic import ValidationInfo, Field

Cuid = Annotated[str, Field(min_length=25, max_length=25)]

DType = TypeVar('DType')
DShape = TypeVar('DShape')


class _TypedArray(np.ndarray, Generic[DType, DShape]):

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, val, field_info: ValidationInfo):
        if not isinstance(val, np.ndarray):
            raise TypeError(f"Expected numpy array. Found {type(val)}")

        actual_dtype = cls.model_fields[field_info.name].type_.__args__[0]

        if val.dtype != actual_dtype:
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
