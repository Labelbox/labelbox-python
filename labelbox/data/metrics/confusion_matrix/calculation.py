from labelbox.data.metrics.iou.calculation import _get_mask_pairs, _get_vector_pairs, miou

from labelbox.data.annotation_types.metrics.confusion_matrix import \
    ConfusionMatrixMetricValue

from labelbox.data.annotation_types.metrics.scalar import ScalarMetricValue
from typing import List, Optional, Tuple, Union
import numpy as np
from ...annotation_types import (ObjectAnnotation, ClassificationAnnotation,
                                 Mask, Geometry, Checklist, Radio)
from ..processing import get_feature_pairs, get_identifying_key, has_no_annotations, has_no_matching_annotations


def confusion_matrix(ground_truths: List[Union[ObjectAnnotation,
                                               ClassificationAnnotation]],
                     predictions: List[Union[ObjectAnnotation,
                                             ClassificationAnnotation]],
                     include_subclasses: bool,
                     iou: float) -> ConfusionMatrixMetricValue:

    annotation_pairs = get_feature_pairs(predictions, ground_truths)
    ious = [
        feature_confusion_matrix(annotation_pair[0], annotation_pair[1],
                                 include_subclasses, iou)
        for annotation_pair in annotation_pairs.values()
    ]
    ious = [iou for iou in ious if iou is not None]

    return None if not len(ious) else np.sum(ious, axis=0).tolist()


def feature_confusion_matrix(
        ground_truths: List[Union[ObjectAnnotation, ClassificationAnnotation]],
        predictions: List[Union[ObjectAnnotation, ClassificationAnnotation]],
        include_subclasses: bool,
        iou: float) -> Optional[ConfusionMatrixMetricValue]:
    if has_no_matching_annotations(ground_truths, predictions):
        return [0, int(len(predictions) > 0), 0, int(len(ground_truths) > 0)]
    elif has_no_annotations(ground_truths, predictions):
        # Note that we could return [0,0,0,0] but that will bloat the imports for no reason
        return None
    elif isinstance(predictions[0].value, Mask):
        return mask_confusion_matrix(ground_truths, predictions, iou,
                                     include_subclasses)
    elif isinstance(predictions[0].value, Geometry):
        return vector_confusion_matrix(ground_truths, predictions, iou,
                                       include_subclasses)
    elif isinstance(predictions[0], ClassificationAnnotation):
        return classification_confusion_matrix(ground_truths, predictions)
    else:
        raise ValueError(
            f"Unexpected annotation found. Found {type(predictions[0].value)}")


def classification_confusion_matrix(
        ground_truths: List[ClassificationAnnotation],
        predictions: List[ClassificationAnnotation]
) -> ConfusionMatrixMetricValue:
    """
    Computes iou score for all features with the same feature schema id.

    Args:
        ground_truths: List of ground truth classification annotations
        predictions: List of prediction classification annotations
    Returns:
        float representing the iou score for the classification
    """

    if has_no_matching_annotations(ground_truths, predictions):
        return [0, int(len(predictions) > 0), 0, int(len(ground_truths) > 0)]
    elif has_no_annotations(
            ground_truths,
            predictions) or len(predictions) > 1 or len(ground_truths) > 1:
        # Note that we could return [0,0,0,0] but that will bloat the imports for no reason
        return None

    prediction, ground_truth = predictions[0], ground_truths[0]

    if type(prediction) != type(ground_truth):
        raise TypeError(
            "Classification features must be the same type to compute agreement. "
            f"Found `{type(prediction)}` and `{type(ground_truth)}`")

    if isinstance(prediction.value, Radio):
        return radio_confusion_matrix(ground_truth.value, prediction.value)
    elif isinstance(prediction.value, Checklist):
        return checklist_confusion_matrix(ground_truth.value, prediction.value)
    else:
        raise ValueError(f"Unsupported subclass. {prediction}.")


def vector_confusion_matrix(ground_truths: List[ObjectAnnotation],
                            predictions: List[ObjectAnnotation],
                            iou: float,
                            include_subclasses: bool,
                            buffer=70.) -> Optional[ConfusionMatrixMetricValue]:
    if has_no_matching_annotations(ground_truths, predictions):
        return [0, int(len(predictions) > 0), 0, int(len(ground_truths) > 0)]
    elif has_no_annotations(ground_truths, predictions):
        return None

    pairs = _get_vector_pairs(ground_truths, predictions, buffer=buffer)
    return object_pair_confusion_matrix(pairs, iou, include_subclasses)


def object_pair_confusion_matrix(
        pairs: List[Tuple[ObjectAnnotation, ObjectAnnotation,
                          ScalarMetricValue]], iou,
        include_subclasses) -> ConfusionMatrixMetricValue:
    pairs.sort(key=lambda triplet: triplet[2], reverse=True)
    prediction_ids = set()
    ground_truth_ids = set()
    matched_predictions = set()
    matched_ground_truths = set()

    for prediction, ground_truth, agreement in pairs:
        prediction_id = id(prediction)
        ground_truth_id = id(ground_truth)
        prediction_ids.add(prediction_id)
        ground_truth_ids.add(ground_truth_id)

        if agreement > iou and \
         prediction_id not in matched_predictions and \
         ground_truth_id not in matched_ground_truths:
            if include_subclasses and (ground_truth.classifications or
                                       prediction.classifications):
                if miou(prediction.classifications,
                        ground_truth.classifications,
                        include_subclasses=False) < 1.:
                    # Incorrect if the subclasses don't 100% agree then there is no match
                    continue
            matched_predictions.add(prediction_id)
            matched_ground_truths.add(ground_truth_id)
    tps = len(matched_ground_truths)
    fps = len(prediction_ids.difference(matched_predictions))
    fns = len(ground_truth_ids.difference(matched_ground_truths))
    # Not defined for object detection.
    tns = 0
    return [tps, fps, tns, fns]


def radio_confusion_matrix(ground_truth: Radio,
                           prediction: Radio) -> ConfusionMatrixMetricValue:
    """
    Calculates confusion between ground truth and predicted radio values

    The way we are calculating confusion matrix metrics:
        - TNs aren't defined because we don't know how many other classes exist ... etc

    When P == L, then we get [1,0,0,0]
    when P != L, we get [0,1,0,1]

    This is because we are aggregating the stats for the entire radio. Not for each class.
    Since we are not tracking TNs (P == L) only adds to TP.
    We are not tracking TNs because the number of TNs is equal to the number of classes which we do not know
    from just looking at the predictions and labels. Also TNs are necessary for precision/recall/f1.
    """
    key = get_identifying_key([prediction.answer], [ground_truth.answer])
    prediction_id = getattr(prediction.answer, key)
    ground_truth_id = getattr(ground_truth.answer, key)

    if prediction_id == ground_truth_id:
        return [1, 0, 0, 0]
    else:
        return [0, 1, 0, 1]


def checklist_confusion_matrix(
        ground_truth: Checklist,
        prediction: Checklist) -> ConfusionMatrixMetricValue:
    """
    Calculates agreement between ground truth and predicted checklist items

    Also not tracking TNs
    """
    key = get_identifying_key(prediction.answer, ground_truth.answer)
    schema_ids_pred = {getattr(answer, key) for answer in prediction.answer}
    schema_ids_label = {getattr(answer, key) for answer in ground_truth.answer}
    agree = schema_ids_label & schema_ids_pred
    all_selected = schema_ids_label | schema_ids_pred
    disagree = all_selected.difference(agree)
    fps = len({x for x in disagree if x in schema_ids_pred})
    fns = len({x for x in disagree if x in schema_ids_label})
    tps = len(agree)
    return [tps, fps, 0, fns]


def mask_confusion_matrix(
        ground_truths: List[ObjectAnnotation],
        predictions: List[ObjectAnnotation], iou,
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
        return [0, int(len(predictions) > 0), 0, int(len(ground_truths) > 0)]
    elif has_no_annotations(ground_truths, predictions):
        return None

    if include_subclasses:
        # This results in a faily drastically different value.
        # If we have subclasses set to True, then this is object detection with masks
        # Otherwise this will flatten the masks.
        # TODO: Make this more apprent in the configuration.
        pairs = _get_mask_pairs(ground_truths, predictions)
        return object_pair_confusion_matrix(
            pairs, iou, include_subclasses=include_subclasses)

    prediction_np = np.max([pred.value.draw(color=1) for pred in predictions],
                           axis=0)
    ground_truth_np = np.max(
        [ground_truth.value.draw(color=1) for ground_truth in ground_truths],
        axis=0)
    if prediction_np.shape != ground_truth_np.shape:
        raise ValueError(
            "Prediction and mask must have the same shape."
            f" Found {prediction_np.shape}/{ground_truth_np.shape}.")

    tp_mask = prediction_np == ground_truth_np == 1
    fp_mask = (prediction_np == 1) & (ground_truth_np == 0)
    fn_mask = (prediction_np == 0) & (ground_truth_np == 1)
    tn_mask = prediction_np == ground_truth_np == 0
    return [np.sum(tp_mask), np.sum(fp_mask), np.sum(fn_mask), np.sum(tn_mask)]
