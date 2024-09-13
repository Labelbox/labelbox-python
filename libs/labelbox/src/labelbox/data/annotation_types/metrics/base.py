from abc import ABC
from typing import Dict, Optional, Any, Union

from pydantic import (
    confloat,
    BaseModel,
    model_serializer,
    field_validator,
    error_wrappers,
)
from pydantic_core import ValidationError, InitErrorDetails

ConfidenceValue = confloat(ge=0, le=1)

MIN_CONFIDENCE_SCORES = 2
MAX_CONFIDENCE_SCORES = 15


class BaseMetric(BaseModel, ABC):
    value: Union[Any, Dict[float, Any]]
    feature_name: Optional[str] = None
    subclass_name: Optional[str] = None
    extra: Dict[str, Any] = {}

    @model_serializer(mode="wrap")
    def serialize_model(self, handler):
        res = handler(self)
        return {k: v for k, v in res.items() if v is not None}

    @field_validator("value")
    def validate_value(cls, value):
        if isinstance(value, Dict):
            if not (
                MIN_CONFIDENCE_SCORES <= len(value) <= MAX_CONFIDENCE_SCORES
            ):
                raise ValueError(
                    f"Number of confidence scores must be greater than\n \
                        or equal to {MIN_CONFIDENCE_SCORES} and less than\n \
                        or equal to {MAX_CONFIDENCE_SCORES}. Found {len(value)}"
                )
        return value
