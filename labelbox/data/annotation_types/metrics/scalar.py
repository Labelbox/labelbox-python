from typing import Dict, Optional, Union
from enum import Enum

from pydantic import confloat

from .base import ConfidenceValue, BaseMetric

ScalarMetricValue = confloat(ge=0, le=100_000_000)
ScalarMetricConfidenceValue = Dict[ConfidenceValue, ScalarMetricValue]


class ScalarMetricAggregation(Enum):
    ARITHMETIC_MEAN = "ARITHMETIC_MEAN"
    GEOMETRIC_MEAN = "GEOMETRIC_MEAN"
    HARMONIC_MEAN = "HARMONIC_MEAN"
    SUM = "SUM"


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

    def dict(self, *args, **kwargs):
        res = super().dict(*args, **kwargs)
        if res.get('metric_name') is None:
            res.pop('aggregation')
        return res
