# type: ignore
from labelbox.data.annotation_types.metrics import ConfusionMatrixMetric
from typing import List, Optional, Union
from ...annotation_types import (Label, ObjectAnnotation,
                                 ClassificationAnnotation)

from ..group import get_feature_pairs
from .calculation import feature_miou
from .calculation import miou
import numpy as np


# You can include subclasses for each of these.
# However, subclasses are only considered matching if there is 100% agreement
# This is most applicable for Radio.

# TODO: Do the top level grouping by all subclasses and support a feature level option..


def confusion_matrix_metric(ground_truths: List[Union[ObjectAnnotation,
                                          ClassificationAnnotation]],
                predictions: List[Union[ObjectAnnotation,
                                        ClassificationAnnotation]],
                include_subclasses=True, iou = 0.5) -> List[ConfusionMatrixMetric]:
    """
    Computes miou between two sets of annotations.
    This will most commonly be used for data row level metrics.
    Each class in the annotation list is weighted equally in the iou score.

    Args:
        ground_truth : Label containing human annotations or annotations known to be correct
        prediction: Label representing model predictions
        include_subclasses (bool): Whether or not to include subclasses in the iou calculation.
            If set to True, the iou between two overlapping objects of the same type is 0 if the subclasses are not the same.
    Returns:
        Returns a list of ScalarMetrics. Will be empty if there were no predictions and labels. Otherwise a single metric will be returned.
    """
    if not (0. < iou < 1.):
        raise ValueError("iou must be between 0 and 1")

    iou = miou(ground_truths, predictions, include_subclasses)
    # If both gt and preds are empty there is no metric
    if iou is None:
        return []

    return [ConfusionMatrixMetric(metric_name="confusion_matrix_{iou}pct_iou", value=iou)]


def feature_confusion_matrix_metric(ground_truths: List[Union[ObjectAnnotation,
                                                  ClassificationAnnotation]],
                        predictions: List[Union[ObjectAnnotation,
                                                ClassificationAnnotation]],
                        include_subclasses=True) -> List[ConfusionMatrixMetric]:
    """
    Computes the miou for each type of class in the list of annotations.

    Args:
        ground_truth : Label containing human annotations or annotations known to be correct
        prediction: Label representing model predictions
        include_subclasses (bool): Whether or not to include subclasses in the iou calculation.
            If set to True, the iou between two overlapping objects of the same type is 0 if the subclasses are not the same.
    Returns:
        Returns a list of ScalarMetrics.
        There will be one metric for each class in the union of ground truth and prediction classes.
    """
    # Classifications are supported because we just take a naive approach to them..
    annotation_pairs = get_feature_pairs(predictions, ground_truths)
    metrics = []
    for key in annotation_pairs:

        value = feature_miou(annotation_pairs[key][0], annotation_pairs[key][1],
                             include_subclasses)
        if value is None:
            continue
        metrics.append(
            ConfusionMatrixMetric(metric_name="iou", feature_name=key, value=value))
    return metrics



def iou_by_tool():
    #... We want to group by tool type.
    #... Otherwise the weighted aggregates could be overpowered.
    #... Since images might be huge, instances will have a few, and classifications will have the fewest.






