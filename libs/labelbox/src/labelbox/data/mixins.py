from typing import Optional, List

from pydantic import BaseModel, field_validator, model_serializer

from labelbox.exceptions import ConfidenceNotSupportedException, CustomMetricsNotSupportedException

from warnings import warn
from labelbox.pydantic_serializers import _feature_serializer


class ConfidenceMixin(BaseModel):
    confidence: Optional[float] = None

    @field_validator("confidence")
    def confidence_valid_float(cls, value):
        if value is None:
            return value
        if not isinstance(value, (int, float)) or not 0 <= value <= 1:
            raise ValueError("must be a number within [0,1] range")
        return value

    @model_serializer(mode="wrap")
    def serialize_model(self, handler):
        res = handler(self)
        res = _feature_serializer(res)
        return res


class ConfidenceNotSupportedMixin:

    def __new__(cls, *args, **kwargs):
        if "confidence" in kwargs:
            raise ConfidenceNotSupportedException(
                "Confidence is not supported for this annotation type yet")
        return super().__new__(cls)


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

    @model_serializer(mode="wrap")
    def serialize_model(self, handler):
        res = handler(self)
        return res


class CustomMetricsNotSupportedMixin:

    def __new__(cls, *args, **kwargs):
        if "custom_metrics" in kwargs:
            raise CustomMetricsNotSupportedException(
                "Custom metrics is not supported for this annotation type yet")
        return super().__new__(cls)
