from typing import Dict, Optional, Union
from typing_extensions import Annotated
from enum import Enum

from pydantic import field_validator
from pydantic.types import confloat

from .base import ConfidenceValue, BaseMetric

ScalarMetricValue = Annotated[float, confloat(ge=0, le=100_000_000)]
ScalarMetricConfidenceValue = Dict[ConfidenceValue, ScalarMetricValue]


class ScalarMetricAggregation(Enum):
    ARITHMETIC_MEAN = "ARITHMETIC_MEAN"
    GEOMETRIC_MEAN = "GEOMETRIC_MEAN"
    HARMONIC_MEAN = "HARMONIC_MEAN"
    SUM = "SUM"


RESERVED_METRIC_NAMES = (
    "true_positive_count",
    "false_positive_count",
    "true_negative_count",
    "false_negative_count",
    "precision",
    "recall",
    "f1",
    "iou",
)


class ScalarMetric(BaseMetric):
    """Class representing scalar metrics

    For backwards compatibility, metric_name is optional.
    The metric_name will be set to a default name in the editor if it is not set.
    This is not recommended and support for empty metric_name fields will be removed.
    aggregation will be ignored without providing a metric name.
    """

    metric_name: Optional[str] = None
    value: Union[ScalarMetricValue, ScalarMetricConfidenceValue]
    aggregation: Optional[ScalarMetricAggregation] = (
        ScalarMetricAggregation.ARITHMETIC_MEAN
    )

    @field_validator("metric_name")
    def validate_metric_name(cls, name: Union[str, None]):
        if name is None:
            return None
        clean_name = name.lower().strip()
        if clean_name in RESERVED_METRIC_NAMES:
            raise ValueError(
                f"`{clean_name}` is a reserved metric name. "
                "Please provide another value for `metric_name`."
            )
        return name
