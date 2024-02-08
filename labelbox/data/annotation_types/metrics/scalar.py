from typing import Dict, Optional, Union
from enum import Enum

from .base import ConfidenceValue, BaseMetric

from labelbox import pydantic_compat

ScalarMetricValue = pydantic_compat.confloat(ge=0, le=100_000_000)
ScalarMetricConfidenceValue = Dict[ConfidenceValue, ScalarMetricValue]


class ScalarMetricAggregation(Enum):
    ARITHMETIC_MEAN = "ARITHMETIC_MEAN"
    GEOMETRIC_MEAN = "GEOMETRIC_MEAN"
    HARMONIC_MEAN = "HARMONIC_MEAN"
    SUM = "SUM"


RESERVED_METRIC_NAMES = ('true_positive_count', 'false_positive_count',
                         'true_negative_count', 'false_negative_count',
                         'precision', 'recall', 'f1', 'iou')


class ScalarMetric(BaseMetric):
    """ Class representing scalar metrics

    For backwards compatibility, metric_name is optional.
    The metric_name will be set to a default name in the editor if it is not set.
    This is not recommended and support for empty metric_name fields will be removed.
    aggregation will be ignored wihtout providing a metric name.
    """
    metric_name: Optional[str] = None
    value: Union[ScalarMetricValue, ScalarMetricConfidenceValue]
    aggregation: ScalarMetricAggregation = ScalarMetricAggregation.ARITHMETIC_MEAN

    @pydantic_compat.validator('metric_name')
    def validate_metric_name(cls, name: Union[str, None]):
        if name is None:
            return None
        clean_name = name.lower().strip()
        if clean_name in RESERVED_METRIC_NAMES:
            raise ValueError(f"`{clean_name}` is a reserved metric name. "
                             "Please provide another value for `metric_name`.")
        return name

    def dict(self, *args, **kwargs):
        res = super().dict(*args, **kwargs)
        if res.get('metric_name') is None:
            res.pop('aggregation')
        return res
