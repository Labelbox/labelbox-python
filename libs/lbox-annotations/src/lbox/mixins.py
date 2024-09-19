from typing import List, Optional

from pydantic import BaseModel, field_validator


class ConfidenceMixin(BaseModel):
    confidence: Optional[float] = None

    @field_validator("confidence")
    def confidence_valid_float(cls, value):
        if value is None:
            return value
        if not isinstance(value, (int, float)) or not 0 <= value <= 1:
            raise ValueError("must be a number within [0,1] range")
        return value


class CustomMetric(BaseModel):
    name: str
    value: float

    @field_validator("name")
    def confidence_valid_float(cls, value):
        if not isinstance(value, str):
            raise ValueError("Name must be a string")
        return value

    @field_validator("value")
    def value_valid_float(cls, value):
        if not isinstance(value, (int, float)):
            raise ValueError("Value must be a number")
        return value


class CustomMetricsMixin(BaseModel):
    custom_metrics: Optional[List[CustomMetric]] = None


