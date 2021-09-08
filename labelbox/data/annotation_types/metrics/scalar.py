from labelbox.data.annotation_types.metrics.aggregations import MetricAggregation
from typing import Any, Dict, Optional, Tuple, Union
from pydantic import BaseModel, Field, validator, confloat


ScalarMetricConfidenceValue = Dict[confloat(ge=0, le=1), float]
ConfusionMatrixMetricConfidenceValue = Dict[confloat(ge=0, le=1), Tuple[int,int,int,int]]


class BaseMetric(BaseModel):
    metric_name: Optional[str] = None
    feature_name: Optional[str] = None
    subclass_name: Optional[str] = None
    extra: Dict[str, Any] = {}


class ScalarMetric(BaseMetric):
    """ Class representing scalar metrics

    For backwards compatibility, metric_name is optional.
    The metric_name will be set to a default name in the editor if it is not set.
    This is not recommended and support for empty metric_name fields will be removed.
    aggregation will be ignored wihtout providing a metric name.
    """
    value: Union[float, ScalarMetricConfidenceValue]
    aggregation: MetricAggregation = MetricAggregation.ARITHMETIC_MEAN

    def dict(self, *args, **kwargs):
        res = super().dict(*args, **kwargs)
        if res['metric_name'] is None:
            res.pop('aggregation')
        return {k: v for k, v in res.items() if v is not None}

    @validator('aggregation')
    def validate_aggregation(cls, aggregation):
        if aggregation == MetricAggregation.CONFUSION_MATRIX:
            raise ValueError("Cannot assign `MetricAggregation.CONFUSION_MATRIX` to `ScalarMetric.aggregation`")



class ConfusionMatrixMetric(BaseMetric):
    """ Class representing confusion matrix metrics.

    In the editor, this provides precision, recall, and f-scores.
    This should be used over multiple scalar metrics so that aggregations are accurate.

    value should be a tuple representing:
      [True Positive Count, False Positive Count, True Negative Count, False Negative Count]

    aggregation cannot be adjusted for confusion matrix metrics.
    """
    value: Union[Tuple[int,int,int,int], ConfusionMatrixMetricConfidenceValue]
    aggregation: MetricAggregation = Field(MetricAggregation.CONFUSION_MATRIX, const = True)

