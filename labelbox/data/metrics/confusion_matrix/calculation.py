from typing import List, Optional, Tuple, Union

import numpy as np

from ..iou.calculation import _get_mask_pairs, _get_vector_pairs, _get_ner_pairs, miou
from ...annotation_types import (ObjectAnnotation, ClassificationAnnotation,
                                 Mask, Geometry, Checklist, Radio, TextEntity,
                                 ScalarMetricValue, ConfusionMatrixMetricValue)
from ..group import (get_feature_pairs, get_identifying_key, has_no_annotations,
                     has_no_matching_annotations)


def confusion_matrix(ground_truths: List[Union[ObjectAnnotation,
                                               ClassificationAnnotation]],
                     predictions: List[Union[ObjectAnnotation,
                                             ClassificationAnnotation]],
                     include_subclasses: bool,
                     iou: float) -> ConfusionMatrixMetricValue:
    """
    Computes the confusion matrix for an arbitrary set of ground truth and predicted annotations.
    It first computes the confusion matrix for each metric and then sums across all classes

    Args:
        ground_truth : Label containing human annotations or annotations known to be correct
        prediction: Label representing model predictions
        include_subclasses (bool): Whether or not to include subclasses in the calculation.
            If set to True, the iou between two overlapping objects of the same type is 0 if the subclasses are not the same.
        iou: minimum overlap between objects for them to count as matching
    Returns:
        confusion matrix as a list: [TP,FP,TN,FN]
        Returns None if there are no annotations in ground_truth or prediction annotations
    """

    annotation_pairs = get_feature_pairs(ground_truths, predictions)
    conf_matrix = [
        feature_confusion_matrix(annotation_pair[0], annotation_pair[1],
                                 include_subclasses, iou)
        for annotation_pair in annotation_pairs.values()
    ]
    matrices = [matrix for matrix in conf_matrix if matrix is not None]
    return None if not len(matrices) else np.sum(matrices, axis=0).tolist()


def feature_confusion_matrix(
        ground_truths: List[Union[ObjectAnnotation, ClassificationAnnotation]],
        predictions: List[Union[ObjectAnnotation, ClassificationAnnotation]],
        include_subclasses: bool,
        iou: float) -> Optional[ConfusionMatrixMetricValue]:
    """
    Computes confusion matrix for all features of the same class.

    Args:
        ground_truths: List of ground truth annotations belonging to the same class.
        predictions: List of annotations  belonging to the same class.
        include_subclasses (bool): Whether or not to include subclasses in the calculation.
            If set to True, the iou between two overlapping objects of the same type is 0 if the subclasses are not the same.
    Returns:
        confusion matrix as a list: [TP,FP,TN,FN]
        Returns None if there are no annotations in ground_truth or prediction annotations
    """
    if has_no_matching_annotations(ground_truths, predictions):
        return [0, len(predictions), 0, len(ground_truths)]
    elif has_no_annotations(ground_truths, predictions):
        return None
    elif isinstance(predictions[0].value, Mask):
        return mask_confusion_matrix(ground_truths, predictions,
                                     include_subclasses, iou)
    elif isinstance(predictions[0].value, Geometry):
        return vector_confusion_matrix(ground_truths, predictions,
                                       include_subclasses, iou)
    elif isinstance(predictions[0].value, TextEntity):
        return ner_confusion_matrix(ground_truths, predictions,
                                    include_subclasses, iou)
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
    Because these predictions and ground truths are already sorted by schema id,
    there can only be one of each (or zero if the classification was not predicted or labeled).

    Args:
        ground_truths: List of ground truth classification annotations
        predictions: List of prediction classification annotations
    Returns:
        confusion matrix as a list: [TP,FP,TN,FN]
        Returns None if there are no annotations in ground_truth or prediction annotations
    """

    if has_no_matching_annotations(ground_truths, predictions):
        return [0, len(predictions), 0, len(ground_truths)]
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
        raise ValueError(
            f"Unsupported subclass. {prediction}. Only Radio and Checklist are supported"
        )


def vector_confusion_matrix(ground_truths: List[ObjectAnnotation],
                            predictions: List[ObjectAnnotation],
                            include_subclasses: bool,
                            iou: float,
                            buffer=70.) -> Optional[ConfusionMatrixMetricValue]:
    """
    Computes confusion matrix for any vector class (point, polygon, line, rectangle).
    Ground truths and predictions should all belong to the same class.

    Args:
        ground_truths: List of ground truth vector annotations
        predictions: List of prediction vector annotations
        iou: minimum overlap between objects for them to count as matching
        include_subclasses (bool): Whether or not to include subclasses in the calculation.
            If set to True, the iou between two overlapping objects of the same type is 0 if the subclasses are not the same.
        buffer: How much to buffer point and lines (used for determining if overlap meets iou threshold )
    Returns:
        confusion matrix as a list: [TP,FP,TN,FN]
         Returns None if there are no annotations in ground_truth or prediction annotations
    """
    if has_no_matching_annotations(ground_truths, predictions):
        return [0, len(predictions), 0, len(ground_truths)]
    elif has_no_annotations(ground_truths, predictions):
        return None

    pairs = _get_vector_pairs(ground_truths, predictions, buffer=buffer)
    return object_pair_confusion_matrix(pairs, include_subclasses, iou)


def object_pair_confusion_matrix(pairs: List[Tuple[ObjectAnnotation,
                                                   ObjectAnnotation,
                                                   ScalarMetricValue]],
                                 include_subclasses: bool,
                                 iou: float) -> ConfusionMatrixMetricValue:
    """
    Computes the confusion matrix for a list of object annotation pairs.
    Performs greedy matching of pairs.

    Args:
        pairs : A list of object annotation pairs with an iou score.
            This is used to determine matching priority (or if objects are matching at all) since objects can only be matched once.
        iou : iou threshold to deterine if objects are matching
    Returns:
        confusion matrix as a list: [TP,FP,TN,FN]
    """
    pairs.sort(key=lambda triplet: triplet[2], reverse=True)
    prediction_ids = set()
    ground_truth_ids = set()
    matched_predictions = set()
    matched_ground_truths = set()

    for ground_truth, prediction, agreement in pairs:
        prediction_id = id(prediction)
        ground_truth_id = id(ground_truth)
        prediction_ids.add(prediction_id)
        ground_truth_ids.add(ground_truth_id)

        if agreement > iou and \
         prediction_id not in matched_predictions and \
         ground_truth_id not in matched_ground_truths:
            if include_subclasses and (ground_truth.classifications or
                                       prediction.classifications):
                if miou(ground_truth.classifications,
                        prediction.classifications,
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

    Calculation:
        - TNs aren't defined because we don't know how many other classes exist
        - When P == L, then we get [1,0,0,0]
        - when P != L, we get [0,1,0,1]

    This is because we are aggregating the stats for the entire radio. Not for each class.
    Since we are not tracking TNs (P == L) only adds to TP.
    We are not tracking TNs because the number of TNs is equal to the number of classes which we do not know
    from just looking at the predictions and labels. Also TNs are necessary for precision/recall/f1.
    """
    key = get_identifying_key([prediction.answer], [ground_truth.answer])
    prediction_id = getattr(prediction.answer, key)
    ground_truth_id = getattr(ground_truth.answer, key)
    return [1, 0, 0, 0] if prediction_id == ground_truth_id else [0, 1, 0, 1]


def checklist_confusion_matrix(
        ground_truth: Checklist,
        prediction: Checklist) -> ConfusionMatrixMetricValue:
    """
    Calculates agreement between ground truth and predicted checklist items:

    Calculation:
        - When a prediction matches a label that counts as a true postivie.
        - When a prediction was made and does not have a corresponding label this is counted as a false postivie
        - When a label does not have a corresponding prediction this is counted as a false negative

    We are also not tracking TNs since we don't know the number of possible classes
     (and they aren't necessary for precision/recall/f1).

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


def mask_confusion_matrix(ground_truths: List[ObjectAnnotation],
                          predictions: List[ObjectAnnotation],
                          include_subclasses: bool,
                          iou: float) -> Optional[ScalarMetricValue]:
    """
    Computes confusion matrix metric for two masks

    Important:
        - If including subclasses in the calculation, then the metrics are computed the same as if it were object detection.
        - Each mask is its own instance. Otherwise this metric is computed as pixel level annotations.

    Args:
        ground_truths: List of ground truth mask annotations
        predictions: List of prediction mask annotations
    Returns:
        confusion matrix as a list: [TP,FP,TN,FN]
    """
    if has_no_matching_annotations(ground_truths, predictions):
        return [0, len(predictions), 0, len(ground_truths)]
    elif has_no_annotations(ground_truths, predictions):
        return None

    if include_subclasses:
        # This results in a faily drastically different value than without subclasses.
        # If we have subclasses set to True, then this is object detection with masks
        # Otherwise this will compute metrics on each pixel.
        pairs = _get_mask_pairs(ground_truths, predictions)
        return object_pair_confusion_matrix(
            pairs, include_subclasses=include_subclasses, iou=iou)

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


def ner_confusion_matrix(ground_truths: List[ObjectAnnotation],
                         predictions: List[ObjectAnnotation],
                         include_subclasses: bool,
                         iou: float) -> Optional[ConfusionMatrixMetricValue]:
    """Computes confusion matrix metric between two lists of TextEntity objects

    Args:
        ground_truths: List of ground truth mask annotations
        predictions: List of prediction mask annotations
    Returns:
        confusion matrix as a list: [TP,FP,TN,FN]
    """
    if has_no_matching_annotations(ground_truths, predictions):
        return [0, len(predictions), 0, len(ground_truths)]
    elif has_no_annotations(ground_truths, predictions):
        return None
    pairs = _get_ner_pairs(ground_truths, predictions)
    return object_pair_confusion_matrix(pairs, include_subclasses, iou)
