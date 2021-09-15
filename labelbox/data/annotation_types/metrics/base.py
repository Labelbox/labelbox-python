from abc import ABC
from pydantic import ValidationError, confloat, BaseModel, validator
from pydantic.error_wrappers import ErrorWrapper
from typing import Dict, Optional, Any, Union

ConfidenceValue = confloat(ge=0, le=1)

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

    @validator('value')
    def validate_value(cls, value):
        if isinstance(value, Dict):
            if not (MIN_CONFIDENCE_SCORES <= len(value) <=
                    MAX_CONFIDENCE_SCORES):
                raise ValidationError([
                    ErrorWrapper(ValueError(
                        "Number of confidence scores must be greater"
                        f" than or equal to {MIN_CONFIDENCE_SCORES} and"
                        f" less than or equal to {MAX_CONFIDENCE_SCORES}. Found {len(value)}"
                    ),
                                 loc='value')
                ], cls)
        return value
