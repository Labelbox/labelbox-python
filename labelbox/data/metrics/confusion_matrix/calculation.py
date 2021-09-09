


from pydantic.utils import truncate

from labelbox.data.annotation_types.metrics.confusion_matrix import \
    ConfusionMatrixMetricValue


from labelbox.data.annotation_types.metrics.scalar import ScalarMetricValue
from typing import List, Optional, Tuple, Union
from shapely.geometry import Polygon
from itertools import product
import numpy as np
from ...annotation_types import (ObjectAnnotation, ClassificationAnnotation,
                                 Mask, Geometry, Point, Line, Checklist, Text,
                                 Radio)
from ..group import get_feature_pairs, get_identifying_key


def confusion_matrix(ground_truths: List[Union[ObjectAnnotation,
                                           ClassificationAnnotation]],
                 predictions: List[Union[ObjectAnnotation,
                                         ClassificationAnnotation]],
                                        iou: float,
                 include_subclasses: bool) -> ConfusionMatrixMetricValue:

    annotation_pairs = get_feature_pairs(predictions, ground_truths)
    ious = [
        feature_confusion_matrix(annotation_pair[0], annotation_pair[1], include_subclasses)
        for annotation_pair in annotation_pairs.values()
    ]
    ious = [iou for iou in ious if iou is not None]
    return None if not len(ious) else np.sum(ious, axis = 0 )



def feature_confusion_matrix(ground_truths: List[Union[ObjectAnnotation,
                                           ClassificationAnnotation]],
                 predictions: List[Union[ObjectAnnotation,
                                         ClassificationAnnotation]],
                                        iou: float,
                 include_subclasses: bool) -> Optional[ConfusionMatrixMetricValue]:
    if _no_matching_annotations(ground_truths, predictions):
        return 0.
    elif _no_annotations(ground_truths, predictions):
        return None
    elif isinstance(predictions[0].value, Mask):
        return mask_confusion_matrix(ground_truths, predictions, include_subclasses)
    elif isinstance(predictions[0].value, Geometry):
        return vector_confusion_matrix(ground_truths, predictions, include_subclasses)
    elif isinstance(predictions[0], ClassificationAnnotation):
        return classification_confusion_matrix(ground_truths, predictions)
    else:
        raise ValueError(
            f"Unexpected annotation found. Found {type(predictions[0].value)}")


def classification_confusion_matrix(ground_truths: List[ClassificationAnnotation],
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
        return text_confusion_matrix(ground_truth.value, prediction.value)
    elif isinstance(prediction.value, Radio):
        return radio_confusion_matrix(ground_truth.value, prediction.value)
    elif isinstance(prediction.value, Checklist):
        return checklist_confusion_matrix(ground_truth.value, prediction.value)
    else:
        raise ValueError(f"Unsupported subclass. {prediction}.")

def vector_confusion_matrix(ground_truths: List[ObjectAnnotation],
                predictions: List[ObjectAnnotation],
                include_subclasses: bool,
                buffer=70.) -> Optional[ConfusionMatrixMetricValue]:
    if _no_matching_annotations(ground_truths, predictions):
        return 0.
    elif _no_annotations(ground_truths, predictions):
        return None

    pairs = _get_vector_pairs(ground_truths, predictions, buffer=buffer)
    pairs.sort(key=lambda triplet: triplet[2], reverse=True)

    prediction_ids = {id(pred) for pred in predictions}
    ground_truth_ids = {id(gt) for gt in ground_truths}
    matched_predictions = set()
    matched_ground_truths = set()

    for prediction, ground_truth, agreement in pairs:
        if id(prediction) not in matched_predictions and id(
                ground_truth) not in matched_ground_truths:
            matched_predictions.add(id(prediction))
            matched_ground_truths.add(id(ground_truth))

    tps = len(matched_ground_truths)
    fps = len(prediction_ids.difference(matched_predictions))
    fns = len(ground_truth_ids.difference(matched_predictions))
    # Not defined for object detection.
    tns = 0
    return [tps, fps, tns, fns]



def _get_vector_pairs(
        ground_truths: List[ObjectAnnotation],
        predictions: List[ObjectAnnotation], buffer: float
) -> List[Tuple[ObjectAnnotation, ObjectAnnotation, ScalarMetricValue]]:
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


def _polygon_iou(poly1: Polygon, poly2: Polygon) -> ScalarMetricValue:
    """Computes iou between two shapely polygons."""
    if poly1.intersects(poly2):
        return poly1.intersection(poly2).area / poly1.union(poly2).area
    return 0.



def radio_confusion_matrix(ground_truth: Radio, prediction: Radio) -> ScalarMetricValue:
    """
    Calculates confusion between ground truth and predicted radio values
    """
    key = get_identifying_key([prediction.answer], [ground_truth.answer])

    return float(getattr(prediction.answer, key) ==
                 getattr(ground_truth.answer, key))


def text_confusion_matrix(ground_truth: Text, prediction: Text) -> ScalarMetricValue:
    """
    Calculates agreement between ground truth and predicted text
    """
    return float(prediction.answer == ground_truth.answer)


def checklist_confusion_matrix(ground_truth: Checklist, prediction: Checklist) -> ScalarMetricValue:
    """
    Calculates agreement between ground truth and predicted checklist items
    """
    key = get_identifying_key(prediction.answer, ground_truth.answer)
    schema_ids_pred = {getattr(answer, key) for answer in prediction.answer}
    schema_ids_label = {
        getattr(answer, key) for answer in ground_truth.answer
    }
    return float(
        len(schema_ids_label & schema_ids_pred) /
        len(schema_ids_label | schema_ids_pred))




def mask_confusion_matrix(ground_truths: List[ObjectAnnotation],
              predictions: List[ObjectAnnotation]) -> Optional[ScalarMetricValue]:
    """
    Computes iou score for all features with the same feature schema id.
    Calculation includes subclassifications.

    Args:
        ground_truths: List of ground truth mask annotations
        predictions: List of prediction mask annotations
    Returns:
        float representing the iou score for the masks
    """
    if _no_matching_annotations(ground_truths, predictions):
        return 0.
    elif _no_annotations(ground_truths, predictions):
        return None

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
    fp_mask = (prediction_np == 1) & (ground_truth_np==0)
    fn_mask = (prediction_np == 0) & (ground_truth_np==1)
    tn_mask = prediction_np == ground_truth_np == 0
    return [np.sum(tp_mask), np.sum(fp_mask), np.sum(fn_mask), np.sum(tn_mask)]



def _no_matching_annotations(ground_truths: List[ObjectAnnotation],
                             predictions: List[ObjectAnnotation]):
    if len(ground_truths) and not len(predictions):
        # No existing predictions but existing ground truths means no matches.
        return True
    elif not len(ground_truths) and len(predictions):
        # No ground truth annotations but there are predictions means no matches
        return True
    return False


def _no_annotations(ground_truths: List[ObjectAnnotation],
                    predictions: List[ObjectAnnotation]):
    return not len(ground_truths) and not len(predictions)



