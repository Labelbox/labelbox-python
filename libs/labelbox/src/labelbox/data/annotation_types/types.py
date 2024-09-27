import sys
from typing import Annotated, Any, Generic, TypeVar

import numpy as np
from packaging import version
from pydantic import ConfigDict, Field, StringConstraints
from pydantic_core import core_schema

DType = TypeVar("DType")
DShape = TypeVar("DShape")


class _TypedArray(np.ndarray, Generic[DType, DShape]):
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


if version.parse(np.__version__) >= version.parse("1.25.0"):
    from typing import GenericAlias

    TypedArray = GenericAlias(_TypedArray, (Any, DType))
elif version.parse(np.__version__) >= version.parse("1.23.0"):
    from numpy._typing import _GenericAlias

    TypedArray = _GenericAlias(_TypedArray, (Any, DType))
elif (
    version.parse("1.22.0")
    <= version.parse(np.__version__)
    < version.parse("1.23.0")
):
    from numpy.typing import _GenericAlias

    TypedArray = _GenericAlias(_TypedArray, (Any, DType))
else:
    TypedArray = _TypedArray[Any, DType]
