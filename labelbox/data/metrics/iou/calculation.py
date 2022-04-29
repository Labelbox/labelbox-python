from typing import List, Optional, Tuple, Union
from itertools import product

from shapely.geometry import Polygon
import numpy as np

from ..group import get_feature_pairs, get_identifying_key, has_no_annotations, has_no_matching_annotations
from ...annotation_types import (ObjectAnnotation, ClassificationAnnotation,
                                 Mask, Geometry, Point, Line, Checklist, Text,
                                 TextEntity, Radio, ScalarMetricValue)


def miou(ground_truths: List[Union[ObjectAnnotation, ClassificationAnnotation]],
         predictions: List[Union[ObjectAnnotation, ClassificationAnnotation]],
         include_subclasses: bool) -> Optional[ScalarMetricValue]:
    """
    Computes miou for an arbitrary set of ground truth and predicted annotations.
    It first computes the iou for each metric and then takes the average (weighting each class equally)

    Args:
        ground_truth : Label containing human annotations or annotations known to be correct
        prediction: Label representing model predictions
        include_subclasses (bool): Whether or not to include subclasses in the iou calculation.
            If set to True, the iou between two overlapping objects of the same type is 0 if the subclasses are not the same.
    Returns:
        float indicating the iou score for all features represented in the annotations passed to this function.
        Returns None if there are no annotations in ground_truth or prediction annotations
    """
    annotation_pairs = get_feature_pairs(predictions, ground_truths)
    ious = [
        feature_miou(annotation_pair[0], annotation_pair[1], include_subclasses)
        for annotation_pair in annotation_pairs.values()
    ]
    ious = [iou for iou in ious if iou is not None]
    return None if not len(ious) else np.mean(ious)


def feature_miou(ground_truths: List[Union[ObjectAnnotation,
                                           ClassificationAnnotation]],
                 predictions: List[Union[ObjectAnnotation,
                                         ClassificationAnnotation]],
                 include_subclasses: bool) -> Optional[ScalarMetricValue]:
    """
    Computes iou score for all features of the same class.

    Args:
        ground_truths: List of ground truth annotations with the same feature schema.
        predictions: List of annotations with the same feature schema.
        include_subclasses (bool): Whether or not to include subclasses in the iou calculation.
            If set to True, the iou between two overlapping objects of the same type is 0 if the subclasses are not the same.
    Returns:
        float representing the iou score for the feature type if score can be computed otherwise None.
    """
    if has_no_matching_annotations(ground_truths, predictions):
        return 0.
    elif has_no_annotations(ground_truths, predictions):
        return None
    elif isinstance(predictions[0].value, Mask):
        return mask_miou(ground_truths, predictions, include_subclasses)
    elif isinstance(predictions[0].value, Geometry):
        return vector_miou(ground_truths, predictions, include_subclasses)
    elif isinstance(predictions[0], ClassificationAnnotation):
        return classification_miou(ground_truths, predictions)
    elif isinstance(predictions[0].value, TextEntity):
        return ner_miou(ground_truths, predictions, include_subclasses)
    else:
        raise ValueError(
            f"Unexpected annotation found. Found {type(predictions[0].value)}")


def vector_miou(ground_truths: List[ObjectAnnotation],
                predictions: List[ObjectAnnotation],
                include_subclasses: bool,
                buffer=70.) -> Optional[ScalarMetricValue]:
    """
    Computes iou score for all features with the same feature schema id.
    Calculation includes subclassifications.

    Args:
        ground_truths: List of ground truth vector annotations
        predictions: List of prediction vector annotations
    Returns:
        float representing the iou score for the feature type.
         If there are no matches then this returns none
    """
    if has_no_matching_annotations(ground_truths, predictions):
        return 0.
    elif has_no_annotations(ground_truths, predictions):
        return None
    pairs = _get_vector_pairs(ground_truths, predictions, buffer=buffer)
    return object_pair_miou(pairs, include_subclasses)


def object_pair_miou(pairs: List[Tuple[ObjectAnnotation, ObjectAnnotation,
                                       ScalarMetricValue]],
                     include_subclasses) -> ScalarMetricValue:
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
                classification_iou = miou(prediction.classifications,
                                          ground_truth.classifications,
                                          include_subclasses=False)
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
              include_subclasses: bool) -> Optional[ScalarMetricValue]:
    """
    Computes iou score for all features with the same feature schema id.
    Calculation includes subclassifications.

    Args:
        ground_truths: List of ground truth mask annotations
        predictions: List of prediction mask annotations
    Returns:
        float representing the iou score for the masks
    """
    if has_no_matching_annotations(ground_truths, predictions):
        return 0.
    elif has_no_annotations(ground_truths, predictions):
        return None

    if include_subclasses:
        pairs = _get_mask_pairs(ground_truths, predictions)
        return object_pair_miou(pairs, include_subclasses=include_subclasses)

    prediction_np = np.max([pred.value.draw(color=1) for pred in predictions],
                           axis=0)
    ground_truth_np = np.max(
        [ground_truth.value.draw(color=1) for ground_truth in ground_truths],
        axis=0)
    if prediction_np.shape != ground_truth_np.shape:
        raise ValueError(
            "Prediction and mask must have the same shape."
            f" Found {prediction_np.shape}/{ground_truth_np.shape}.")

    return _mask_iou(ground_truth_np, prediction_np)


def classification_miou(
        ground_truths: List[ClassificationAnnotation],
        predictions: List[ClassificationAnnotation]) -> ScalarMetricValue:
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
        raise ValueError(f"Unsupported subclass. {prediction}.")


def radio_iou(ground_truth: Radio, prediction: Radio) -> ScalarMetricValue:
    """
    Calculates agreement between ground truth and predicted radio values
    """
    key = get_identifying_key([prediction.answer], [ground_truth.answer])
    return float(
        getattr(prediction.answer, key) == getattr(ground_truth.answer, key))


def text_iou(ground_truth: Text, prediction: Text) -> ScalarMetricValue:
    """
    Calculates agreement between ground truth and predicted text
    """
    return float(prediction.answer == ground_truth.answer)


def checklist_iou(ground_truth: Checklist,
                  prediction: Checklist) -> ScalarMetricValue:
    """
    Calculates agreement between ground truth and predicted checklist items
    """
    key = get_identifying_key(prediction.answer, ground_truth.answer)
    schema_ids_pred = {getattr(answer, key) for answer in prediction.answer}
    schema_ids_label = {getattr(answer, key) for answer in ground_truth.answer}
    return float(
        len(schema_ids_label & schema_ids_pred) /
        len(schema_ids_label | schema_ids_pred))


def _get_vector_pairs(
    ground_truths: List[ObjectAnnotation], predictions: List[ObjectAnnotation],
    buffer: float
) -> List[Tuple[ObjectAnnotation, ObjectAnnotation, ScalarMetricValue]]:
    """
    # Get iou score for all pairs of ground truths and predictions
    """
    pairs = []
    for ground_truth, prediction in product(ground_truths, predictions):
        if isinstance(prediction.value, Geometry) and isinstance(
                ground_truth.value, Geometry):
            if isinstance(prediction.value, (Line, Point)):

                score = _polygon_iou(prediction.value.shapely.buffer(buffer),
                                     ground_truth.value.shapely.buffer(buffer))
            else:
                score = _polygon_iou(prediction.value.shapely,
                                     ground_truth.value.shapely)
            pairs.append((ground_truth, prediction, score))
    return pairs


def _get_mask_pairs(
    ground_truths: List[ObjectAnnotation], predictions: List[ObjectAnnotation]
) -> List[Tuple[ObjectAnnotation, ObjectAnnotation, ScalarMetricValue]]:
    """
    # Get iou score for all pairs of ground truths and predictions
    """
    pairs = []
    for ground_truth, prediction in product(ground_truths, predictions):
        if isinstance(prediction.value, Mask) and isinstance(
                ground_truth.value, Mask):
            score = _mask_iou(prediction.value.draw(color=1),
                              ground_truth.value.draw(color=1))
            pairs.append((ground_truth, prediction, score))
    return pairs


def _polygon_iou(poly1: Polygon, poly2: Polygon) -> ScalarMetricValue:
    """Computes iou between two shapely polygons."""
    poly1, poly2 = _ensure_valid_poly(poly1), _ensure_valid_poly(poly2)
    if poly1.intersects(poly2):
        return poly1.intersection(poly2).area / poly1.union(poly2).area
    return 0.


def _ensure_valid_poly(poly):
    if not poly.is_valid:
        return poly.buffer(0)
    return poly


def _mask_iou(mask1: np.ndarray, mask2: np.ndarray) -> ScalarMetricValue:
    """Computes iou between two binary segmentation masks."""
    return np.sum(mask1 & mask2) / np.sum(mask1 | mask2)


def _get_ner_pairs(
    ground_truths: List[ObjectAnnotation], predictions: List[ObjectAnnotation]
) -> List[Tuple[ObjectAnnotation, ObjectAnnotation, ScalarMetricValue]]:
    """Get iou score for all possible pairs of ground truths and predictions"""
    pairs = []
    for ground_truth, prediction in product(ground_truths, predictions):
        score = _ner_iou(ground_truth.value, prediction.value)
        pairs.append((ground_truth, prediction, score))
    return pairs


def _ner_iou(ner1: TextEntity, ner2: TextEntity):
    """Computes iou between two text entity annotations"""
    intersection_start, intersection_end = max(ner1.start, ner2.start), min(
        ner1.end, ner2.end)
    union_start, union_end = min(ner1.start,
                                 ner2.start), max(ner1.end, ner2.end)
    #edge case of only one character in text
    if union_start == union_end:
        return 1
    #if there is no intersection
    if intersection_start > intersection_end:
        return 0
    return (intersection_end - intersection_start) / (union_end - union_start)


def ner_miou(ground_truths: List[ObjectAnnotation],
             predictions: List[ObjectAnnotation],
             include_subclasses: bool) -> Optional[ScalarMetricValue]:
    """
    Computes iou score for all features with the same feature schema id.
    Calculation includes subclassifications.

    Args:
        ground_truths: List of ground truth ner annotations
        predictions: List of prediction ner annotations
    Returns:
        float representing the iou score for the feature type.
         If there are no matches then this returns none
    """
    if has_no_matching_annotations(ground_truths, predictions):
        return 0.
    elif has_no_annotations(ground_truths, predictions):
        return None
    pairs = _get_ner_pairs(ground_truths, predictions)
    return object_pair_miou(pairs, include_subclasses)