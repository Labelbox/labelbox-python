from typing import Optional, List

from labelbox import pydantic_compat

from labelbox.exceptions import ConfidenceNotSupportedException, CustomMetricsNotSupportedException


class ConfidenceMixin(pydantic_compat.BaseModel):
    confidence: Optional[float] = None

    @pydantic_compat.validator("confidence")
    def confidence_valid_float(cls, value):
        if value is None:
            return value
        if not isinstance(value, (int, float)) or not 0 <= value <= 1:
            raise ValueError("must be a number within [0,1] range")
        return value

    def dict(self, *args, **kwargs):
        res = super().dict(*args, **kwargs)
        if "confidence" in res and res["confidence"] is None:
            res.pop("confidence")
        return res


class ConfidenceNotSupportedMixin:

    def __new__(cls, *args, **kwargs):
        if "confidence" in kwargs:
            raise ConfidenceNotSupportedException(
                "Confidence is not supported for this annotation type yet")
        return super().__new__(cls)


class CustomMetric(pydantic_compat.BaseModel):
    name: str
    value: float

    @pydantic_compat.validator("name")
    def confidence_valid_float(cls, value):
        if not isinstance(value, str):
            raise ValueError("Name must be a string")
        return value

    @pydantic_compat.validator("value")
    def value_valid_float(cls, value):
        if not isinstance(value, (int, float)):
            raise ValueError("Value must be a number")
        return value


class CustomMetricsMixin(pydantic_compat.BaseModel):
    custom_metrics: Optional[List[CustomMetric]] = None

    def dict(self, *args, **kwargs):
        res = super().dict(*args, **kwargs)

        if "customMetrics" in res and res["customMetrics"] is None:
            res.pop("customMetrics")

        if "custom_metrics" in res and res["custom_metrics"] is None:
            res.pop("custom_metrics")

        return res


class CustomMetricsNotSupportedMixin:

    def __new__(cls, *args, **kwargs):
        if "custom_metrics" in kwargs:
            raise CustomMetricsNotSupportedException(
                "Custom metrics is not supported for this annotation type yet")
        return super().__new__(cls)
