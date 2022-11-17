# type: ignore
from labelbox.data.annotation_types.metrics.scalar import ScalarMetric
from typing import List, Optional, Union
from ...annotation_types import (Label, ObjectAnnotation,
                                 ClassificationAnnotation)

from ..group import get_feature_pairs
from .calculation import feature_miou
from .calculation import miou


def miou_metric(ground_truths: List[Union[ObjectAnnotation,
                                          ClassificationAnnotation]],
                predictions: List[Union[ObjectAnnotation,
                                        ClassificationAnnotation]],
                include_subclasses=False) -> List[ScalarMetric]:
    """
    Computes miou between two sets of annotations.
    These annotations should relate to the same data (image/video).
    Each class in the annotation list is weighted equally in the iou score.

    Args:
        ground_truth : Label containing human annotations or annotations known to be correct
        prediction: Label representing model predictions
        include_subclasses (bool): Whether or not to include subclasses in the iou calculation.
            If set to True, the iou between two overlapping objects of the same type is 0 if the subclasses are not the same.
    Returns:
        Returns a list of ScalarMetrics. Will be empty if there were no predictions and labels. Otherwise a single metric will be returned.
    """
    iou = miou(ground_truths, predictions, include_subclasses)
    # If both gt and preds are empty there is no metric
    if iou is None:
        return []
    return [ScalarMetric(metric_name="custom_iou", value=iou)]


def feature_miou_metric(ground_truths: List[Union[ObjectAnnotation,
                                                  ClassificationAnnotation]],
                        predictions: List[Union[ObjectAnnotation,
                                                ClassificationAnnotation]],
                        include_subclasses=True) -> List[ScalarMetric]:
    """
    Computes the miou for each type of class in the list of annotations.
    These annotations should relate to the same data (image/video).

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
            ScalarMetric(metric_name="custom_iou",
                         feature_name=key,
                         value=value))
    return metrics


def data_row_miou(ground_truth: Label,
                  prediction: Label,
                  include_subclasses=False) -> Optional[float]:
    """

    This function is no longer supported. Use miou() for raw values or miou_metric() for the metric

    Calculates iou for two labels corresponding to the same data row.

    Args:
        ground_truth : Label containing human annotations or annotations known to be correct
        prediction: Label representing model predictions
    Returns:
        float indicating the iou score for this data row.
        Returns None if there are no annotations in ground_truth or prediction Labels
    """
    return miou(ground_truth.annotations, prediction.annotations,
                include_subclasses)
