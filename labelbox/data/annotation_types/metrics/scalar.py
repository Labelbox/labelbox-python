from labelbox.data.annotation_types.metrics.aggregations import MetricAggregation
from typing import Any, Dict, Optional
from pydantic import BaseModel


class ScalarMetric(BaseModel):
    """ Class representing metrics """
    value: float
    extra: Dict[str, Any] = {}


class CustomScalarMetric(BaseModel):
    metric_name: str
    metric_value: float
    feature_name: Optional[str] = None
    subclass_name: Optional[str] = None
    aggregation: MetricAggregation = MetricAggregation.ARITHMETIC_MEAN
    extra: Dict[str, Any] = {}


# TODO: Create a metric type that is used once....
