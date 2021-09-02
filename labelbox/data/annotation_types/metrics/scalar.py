from labelbox.data.annotation_types.metrics.aggregations import MetricAggregation
from typing import Any, Dict, Optional
from pydantic import BaseModel


class ScalarMetric(BaseModel):
    """ Class representing metrics

    # For backwards compatibility, metric_name is optional. This will eventually be deprecated
    # The metric_name will be set to a default name in the editor if it is not set.

    """
    value: float
    metric_name: Optional[str] = None
    feature_name: Optional[str] = None
    subclass_name: Optional[str] = None
    aggregation: MetricAggregation = MetricAggregation.ARITHMETIC_MEAN
    extra: Dict[str, Any] = {}


