# type: ignore
from labelbox.data.annotation_types.metrics.scalar import ScalarMetric
from typing import Dict, List, Optional, Tuple, Union
from shapely.geometry import Polygon
from itertools import product
import numpy as np
from collections import defaultdict
from ..annotation_types.feature import FeatureSchema
from ..annotation_types import (Label, ObjectAnnotation,
                                ClassificationAnnotation, Mask, Geometry, Point,
                                Line, Checklist, Text, Radio)

from .utils import get_feature_pairs
"""
Instead of these functions accepting labels they should accept annotations..
Then we can add a helper for applying functions across pred and label combinations..

We will get stats for each and the stats will support flattening


data_row_iou()

Is it even possible to return a None? If both are none then they won't have keys..
Everything will have types. That is the MO of the

Nike - Somehow getting issue with empty masks. idk wtf
"""


# TODO: What should we call this?
# We should be returning these objects..
def data_row_miou_v2(ground_truth: Label,
                     prediction: Label,
                     include_subclasses=True) -> List[ScalarMetric]:
    feature_ious = data_row_miou(ground_truth.annotations,
                                 prediction.annotations, include_subclasses)
    return [ScalarMetric(metric_name="iou", value=feature_ious)]


def features_miou(ground_truths: List[Union[ObjectAnnotation,
                                            ClassificationAnnotation]],
                  predictions: List[Union[ObjectAnnotation,
                                          ClassificationAnnotation]],
                  include_subclasses=True) -> List[ScalarMetric]:
    """
    Groups annotations by feature_schema_id or name (which is available), calculates iou score and returns the mean across all features.

    Args:
        ground_truth : Label containing human annotations or annotations known to be correct
        prediction: Label representing model predictions
    Returns:
        float indicating the iou score for all features represented in the annotations passed to this function.
        Returns None if there are no annotations in ground_truth or prediction annotations
    """
    # Classifications are supported because we just take a naive approach to them..
    annotation_pairs = get_feature_pairs(predictions, ground_truths)
    return [
        ScalarMetric(metric_name="iou",
                     value=feature_miou(annotation_pair[0], annotation_pair[1],
                                        include_subclasses))
        for annotation_pair in annotation_pairs
    ]


def data_row_miou(ground_truth: Label,
                  prediction: Label,
                  include_subclasses=True) -> Optional[float]:
    """
    Calculate iou for two labels corresponding to the same data row.

    Args:
        ground_truth : Label containing human annotations or annotations known to be correct
        prediction: Label representing model predictions
    Returns:
        float indicating the iou score for this data row.
        Returns None if there are no annotations in ground_truth or prediction Labels
    """
    feature_ious = features_miou(ground_truth.annotations,
                                 prediction.annotations, include_subclasses)
    return average_ious(
        {feature.metric_name: feature.value for feature in feature_ious})


def average_ious(feature_ious: Dict[str, Optional[float]]) -> Optional[float]:
    ious = [iou for iou in feature_ious.values() if iou is not None]
    return None if not len(ious) else np.mean(ious)


def feature_miou(ground_truths: List[Union[ObjectAnnotation,
                                           ClassificationAnnotation]],
                 predictions: List[Union[ObjectAnnotation,
                                         ClassificationAnnotation]],
                 include_subclasses: bool) -> Optional[float]:
    """
    Computes iou score for all features with the same feature schema id.

    Args:
        ground_truths: List of ground truth annotations with the same feature schema.
        predictions: List of annotations with the same feature schema.
    Returns:
        float representing the iou score for the feature type if score can be computed otherwise None.
    """
    if len(ground_truths) and not len(predictions):
        # No existing predictions but existing ground truths means no matches.
        return 0.
    elif not len(ground_truths) and len(predictions):
        # No ground truth annotations but there are predictions means no matches
        return 0.
    elif not len(ground_truths) and not len(
            predictions
    ):  #TODO: This shouldn't run at all for subclasses. Otherwise it should return 1.
        # Ignore examples that do not have any annotations or predictions
        # This could maybe be counted as correct but could also skew the stats..
        return  # Undefined (neither wrong nor right. )
    elif isinstance(predictions[0].value, Mask):
        return mask_miou(ground_truths, predictions, include_subclasses)
    elif isinstance(predictions[0].value, Geometry):
        return vector_miou(ground_truths, predictions, include_subclasses)
    elif isinstance(predictions[0], ClassificationAnnotation):
        return classification_miou(ground_truths, predictions)
    else:
        raise ValueError(
            f"Unexpected annotation found. Found {type(predictions[0].value)}")


def vector_miou(ground_truths: List[ObjectAnnotation],
                predictions: List[ObjectAnnotation],
                buffer=70.,
                include_subclasses=True) -> float:
    """
    Computes iou score for all features with the same feature schema id.
    Calculation includes subclassifications.

    Args:
        ground_truths: List of ground truth vector annotations
        predictions: List of prediction vector annotations
    Returns:
        float representing the iou score for the feature type
    """
    pairs = _get_vector_pairs(ground_truths, predictions, buffer=buffer)
    pairs.sort(key=lambda triplet: triplet[2], reverse=True)
    solution_agreements = []
    solution_features = set()
    all_features = set()
    for prediction, ground_truth, agreement in pairs:
        all_features.update({id(prediction), id(ground_truth)})
        if id(prediction) not in solution_features and id(
                ground_truth) not in solution_features:
            solution_features.update({id(prediction), id(ground_truth)})
            if include_subclasses:
                classification_iou = average_ious(
                    get_iou_across_features(prediction.classifications,
                                            ground_truth.classifications))
                classification_iou = classification_iou if classification_iou is not None else agreement
                solution_agreements.append(
                    (agreement + classification_iou) / 2.)
            else:
                solution_agreements.append(agreement)

    # Add zeros for unmatched Features
    solution_agreements.extend([0.0] *
                               (len(all_features) - len(solution_features)))
    return np.mean(solution_agreements)


def mask_miou(ground_truths: List[ObjectAnnotation],
              predictions: List[ObjectAnnotation],
              include_subclasses=True) -> float:
    """
    Computes iou score for all features with the same feature schema id.
    Calculation includes subclassifications.

    Args:
        ground_truths: List of ground truth mask annotations
        predictions: List of prediction mask annotations
    Returns:
        float representing the iou score for the masks
    """
    prediction_np = np.max([pred.value.draw(color=1) for pred in predictions],
                           axis=0)
    ground_truth_np = np.max(
        [ground_truth.value.draw(color=1) for ground_truth in ground_truths],
        axis=0)
    if prediction_np.shape != ground_truth_np.shape:
        raise ValueError(
            "Prediction and mask must have the same shape."
            f" Found {prediction_np.shape}/{ground_truth_np.shape}.")

    agreement = _mask_iou(ground_truth_np, prediction_np)
    if not include_subclasses:
        return agreement

    prediction_classifications = []
    for prediction in predictions:
        prediction_classifications.extend(prediction.classifications)
    ground_truth_classifications = []
    for ground_truth in ground_truths:
        ground_truth_classifications.extend(ground_truth.classifications)

    classification_iou = get_iou_across_features(ground_truth_classifications,
                                                 prediction_classifications)

    classification_iou = classification_iou if classification_iou is not None else agreement
    return (agreement + classification_iou) / 2.


def classification_miou(ground_truths: List[ClassificationAnnotation],
                        predictions: List[ClassificationAnnotation]) -> float:
    """
    Computes iou score for all features with the same feature schema id.

    Args:
        ground_truths: List of ground truth classification annotations
        predictions: List of prediction classification annotations
    Returns:
        float representing the iou score for the classification
    """

    if len(predictions) != len(ground_truths) != 1:
        return 0.

    prediction, ground_truth = predictions[0], ground_truths[0]

    if type(prediction) != type(ground_truth):
        raise TypeError(
            "Classification features must be the same type to compute agreement. "
            f"Found `{type(prediction)}` and `{type(ground_truth)}`")

    if isinstance(prediction.value, Text):
        return text_iou(ground_truth.value, prediction.value)
    elif isinstance(prediction.value, Radio):
        return radio_iou(ground_truth.value, prediction.value)
    elif isinstance(prediction.value, Checklist):
        return checklist_iou(ground_truth.value, prediction.value)
    else:
        raise ValueError(f"Unexpected subclass. {prediction}")


def radio_iou(ground_truth: Radio, prediction: Radio) -> float:
    """
    Calculates agreement between ground truth and predicted radio values
    """
    return float(prediction.answer.feature_schema_id ==
                 ground_truth.answer.feature_schema_id)


def text_iou(ground_truth: Text, prediction: Text) -> float:
    """
    Calculates agreement between ground truth and predicted text
    """
    return float(prediction.answer == ground_truth.answer)


def checklist_iou(ground_truth: Checklist, prediction: Checklist) -> float:
    """
    Calculates agreement between ground truth and predicted checklist items
    """
    schema_ids_pred = {answer.feature_schema_id for answer in prediction.answer}
    schema_ids_label = {
        answer.feature_schema_id for answer in ground_truth.answer
    }
    return float(
        len(schema_ids_label & schema_ids_pred) /
        len(schema_ids_label | schema_ids_pred))


def _get_vector_pairs(
        ground_truths: List[ObjectAnnotation],
        predictions: List[ObjectAnnotation], buffer: float
) -> List[Tuple[ObjectAnnotation, ObjectAnnotation, float]]:
    """
    # Get iou score for all pairs of ground truths and predictions
    """
    pairs = []
    for prediction, ground_truth in product(predictions, ground_truths):
        if isinstance(prediction.value, Geometry) and isinstance(
                ground_truth.value, Geometry):
            if isinstance(prediction.value, (Line, Point)):
                score = _polygon_iou(prediction.value.shapely.buffer(buffer),
                                     ground_truth.value.shapely.buffer(buffer))
            else:
                score = _polygon_iou(prediction.value.shapely,
                                     ground_truth.value.shapely)
            pairs.append((prediction, ground_truth, score))
    return pairs


def _polygon_iou(poly1: Polygon, poly2: Polygon) -> float:
    """Computes iou between two shapely polygons."""
    if poly1.intersects(poly2):
        return poly1.intersection(poly2).area / poly1.union(poly2).area
    return 0.


def _mask_iou(mask1: np.ndarray, mask2: np.ndarray) -> float:
    """Computes iou between two binary segmentation masks."""
    return np.sum(mask1 & mask2) / np.sum(mask1 | mask2)
