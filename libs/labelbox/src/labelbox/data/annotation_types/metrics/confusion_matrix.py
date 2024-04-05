from enum import Enum
from typing import Tuple, Dict, Union

from labelbox import pydantic_compat

from .base import ConfidenceValue, BaseMetric

Count = pydantic_compat.conint(ge=0, le=1e10)

ConfusionMatrixMetricValue = Tuple[Count, Count, Count, Count]
ConfusionMatrixMetricConfidenceValue = Dict[ConfidenceValue,
                                            ConfusionMatrixMetricValue]


class ConfusionMatrixAggregation(Enum):
    CONFUSION_MATRIX = "CONFUSION_MATRIX"


class ConfusionMatrixMetric(BaseMetric):
    """ Class representing confusion matrix metrics.

    In the editor, this provides precision, recall, and f-scores.
    This should be used over multiple scalar metrics so that aggregations are accurate.

    Value should be a tuple representing:
      [True Positive Count, False Positive Count, True Negative Count, False Negative Count]

    aggregation cannot be adjusted for confusion matrix metrics.
    """
    metric_name: str
    value: Union[ConfusionMatrixMetricValue,
                 ConfusionMatrixMetricConfidenceValue]
    aggregation: ConfusionMatrixAggregation = pydantic_compat.Field(
        ConfusionMatrixAggregation.CONFUSION_MATRIX, const=True)
