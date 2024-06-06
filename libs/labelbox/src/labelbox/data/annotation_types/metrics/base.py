from abc import ABC
from typing import Dict, Optional, Any, Union
from labelbox.typing_imports import Annotated

from pydantic import BaseModel, field_validator, Field, ValidationError

ConfidenceValue = Annotated[float, Field(ge=0, le=1)]

MIN_CONFIDENCE_SCORES = 2
MAX_CONFIDENCE_SCORES = 15


class BaseMetric(BaseModel, ABC):
    value: Union[Any, Dict[float, Any]]
    feature_name: Optional[str] = None
    subclass_name: Optional[str] = None
    extra: Dict[str, Any] = {}

    def dict(self, *args, **kwargs):
        res = super().dict(*args, **kwargs)
        return {k: v for k, v in res.items() if v is not None}

    @field_validator('value')
    @classmethod
    def validate_value(cls, value):
        if isinstance(value, Dict):
            if not (MIN_CONFIDENCE_SCORES <= len(value) <=
                    MAX_CONFIDENCE_SCORES):
                raise ValidationError([
                    ValueError(
                        "Number of confidence scores must be greater"
                        f" than or equal to {MIN_CONFIDENCE_SCORES} and"
                        f" less than or equal to {MAX_CONFIDENCE_SCORES}. Found {len(value)}"
                    ),
                ], cls)
        return value
