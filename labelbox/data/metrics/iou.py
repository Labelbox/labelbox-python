# type: ignore
from labelbox.data.annotation_types.classification.classification import Checklist, Text, Radio
from labelbox.data.annotation_types import feature
from typing import Dict, Any, List, Optional, Tuple, Union
from shapely.geometry import Polygon
from itertools import product
import numpy as np
from collections import defaultdict

from ..annotation_types import Label, ObjectAnnotation, ClassificationAnnotation, Mask, Geometry
from ..annotation_types.annotation import BaseAnnotation
from labelbox.data import annotation_types


def mask_miou(predictions: List[Mask],
              ground_truths: List[Mask],
              resize_height=None,
              resize_width=None) -> float:
    """
    Creates prediction and label binary mask for all features with the same feature schema id.
    Masks are flattened and treated as one class.
    If you want to treat each object as an instance then convert each mask to a polygon annotation.

    Args:
        predictions: List of masks objects
        ground_truths: List of masks objects
    Returns:
        float indicating iou score
    """
    prediction_np = np.max([
        pred.raster(binary=True, height=resize_height, width=resize_width)
        for pred in predictions
    ],
                           axis=0)
    ground_truth_np = np.max([
        ground_truth.raster(
            binary=True, height=resize_height, width=resize_width)
        for ground_truth in ground_truths
    ],
                             axis=0)
    if prediction_np.shape != ground_truth_np.shape:
        raise ValueError(
            "Prediction and mask must have the same shape."
            f" Found {prediction_np.shape}/{ground_truth_np.shape}."
            " Add resize params to fix this.")
    return _mask_iou(ground_truth_np, prediction_np)


def classification_miou(predictions: List[ClassificationAnnotation],
                        labels: List[ClassificationAnnotation]) -> float:
    """
    Computes iou for classification features.

    Args:
        prediction : list of predictions for a particular feature schema ( should have a max of one ).
        label : list of predictions for a particular feature schema ( should have a max of one ).
    Returns:
        float indicating iou score.

    """

    if len(predictions) != len(labels) != 1:
        return 0.

    prediction, label = predictions[0], labels[0]

    if type(prediction) != type(label):
        raise TypeError(
            "Classification features must be the same type to compute agreement. "
            f"Found `{type(prediction)}` and `{type(label)}`")

    if isinstance(prediction.value, Text):
        return float(prediction.value.answer == label.value.answer)
    elif isinstance(prediction.value, Radio):
        return float(
            prediction.value.answer.schema_id == label.value.answer.schema_id)
    elif isinstance(prediction.value, Checklist):
        schema_ids_pred = {
            answer.schema_id for answer in prediction.value.answer
        }
        schema_ids_label = {answer.schema_id for answer in label.value.answer}
        return float(
            len(schema_ids_label & schema_ids_pred) /
            len(schema_ids_label | schema_ids_pred))
    else:
        raise ValueError(f"Unexpected subclass. {prediction}")


def subclassification_miou(
        subclass_predictions: List[ClassificationAnnotation],
        subclass_labels: List[ClassificationAnnotation]) -> Optional[float]:
    """

    Computes subclass iou score between two vector tools that were matched.

    Arg:
        subclass_predictions: All subclasses for a particular vector feature inference
        subclass_labels : All subclass labels for a label that matched with the vector feature inference.

    Returns:
        miou across all subclasses.
    """

    subclass_predictions = _create_schema_lookup(subclass_predictions)
    subclass_labels = _create_schema_lookup(subclass_labels)
    feature_schemas = set(subclass_predictions.keys()).union(
        set(subclass_labels.keys()))
    classification_iou = [
        feature_miou(subclass_predictions[feature_schema],
                     subclass_labels[feature_schema])
        for feature_schema in feature_schemas
    ]
    classification_iou = [x for x in classification_iou if x is not None]
    return None if not len(classification_iou) else np.mean(classification_iou)


def vector_miou(predictions: List[Geometry], labels: List[Geometry],
                include_subclasses) -> float:
    """
    Computes an iou score for vector tools.

    Args:
        predictions: List of predictions that correspond to the same feature schema
        labels: List of labels that correspond to the same feature schema
        include_subclasses: Whether or not to include the subclasses in the calculation.
    Returns:
        miou score for the feature schema

    """
    pairs = _get_vector_pairs(predictions, labels)
    pairs.sort(key=lambda triplet: triplet[2], reverse=True)
    solution_agreements = []
    solution_features = set()
    all_features = set()
    for pred, label, agreement in pairs:
        all_features.update({pred.uuid, label.uuid})
        if pred.uuid not in solution_features and label.uuid not in solution_features:
            solution_features.update({pred.uuid, label.uuid})
            if include_subclasses:
                classification_iou = subclassification_miou(
                    pred.classifications, label.classifications)
                classification_iou = classification_iou if classification_iou is not None else agreement
                solution_agreements.append(
                    (agreement + classification_iou) / 2.)
            else:
                solution_agreements.append(agreement)

    # Add zeros for unmatched Features
    solution_agreements.extend([0.0] *
                               (len(all_features) - len(solution_features)))
    return np.mean(solution_agreements)


def feature_miou(predictions: List[Union[ObjectAnnotation,
                                         ClassificationAnnotation]],
                 labels: List[Union[ObjectAnnotation,
                                    ClassificationAnnotation]],
                 include_subclasses=True) -> Optional[float]:
    """
    Computes iou score for all features with the same feature schema id.

    Args:
        predictions: List of annotations with the same feature schema.
        labels: List of labels with the same feature schema.
    Returns:
        float representing the iou score for the feature type if score can be computed otherwise None.
    """
    if len(predictions):
        keys = predictions[0]
    elif len(labels):
        # No existing predictions but existing labels means no matches.
        return 0.0
    else:
        # Ignore examples that do not have any labels or predictions
        return None

    if isinstance(predictions[0].value, Mask):
        # TODO: A mask can have subclasses too.. Why are we treating this differently?
        return mask_miou(predictions, labels)
    elif isinstance(predictions[0].value, Geometry):
        return vector_miou(predictions,
                           labels,
                           include_subclasses=include_subclasses)
    elif isinstance(predictions[0].value, ClassificationAnnotation):
        return classification_miou(predictions, labels)
    else:
        raise ValueError(
            f"Unexpected annotation found. Found {type(predictions[0])}")


def _create_schema_lookup(annotations: List[BaseAnnotation]):
    grouped_annotations = defaultdict(list)
    for annotation in annotations:
        grouped_annotations[annotation.schema_id] = annotation
    return grouped_annotations


def data_row_miou(ground_truth: Label,
                  predictions: Label,
                  include_classifications=True,
                  include_subclasses=True) -> float:
    """
    # At this point all object should have schema ids.

    Args:
        label_content : one row from the bulk label export - `project.export_labels()`
        ndjsons: Model predictions in the ndjson format specified here (https://docs.labelbox.com/data-model/en/index-en#annotations)
        include_classifications: Whether or not to factor top level classifications into the iou score.
        include_subclassifications: Whether or not to factor in subclassifications into the iou score
    Returns:
        float indicating the iou score for this data row.
    """
    annotation_types = None if include_classifications else Geometry
    prediction_annotations = predictions.get_annotations_by_attr(
        attr="name", annotation_types=annotation_types)
    ground_truth_annotations = ground_truth.get_annotations_by_attr(
        attr="name", annotation_types=annotation_types)
    feature_schemas = set(prediction_annotations.keys()).union(
        set(ground_truth_annotations.keys()))
    ious = [
        feature_miou(prediction_annotations[feature_schema],
                     ground_truth_annotations[feature_schema],
                     include_subclasses=include_subclasses)
        for feature_schema in feature_schemas
    ]
    ious = [iou for iou in ious if iou is not None]
    if not ious:
        return None
    return np.mean(ious)


def _get_vector_pairs(predictions: List[Geometry],
                      ground_truths: List[Geometry]):
    """
    # Get iou score for all pairs of labels and predictions
    """
    return [(prediction, ground_truth,
             _polygon_iou(prediction.shapely, ground_truth.shapely))
            for prediction, ground_truth in product(predictions, ground_truths)]


def _polygon_iou(poly1: Polygon, poly2: Polygon) -> float:
    """Computes iou between two shapely polygons."""
    if poly1.intersects(poly2):
        return poly1.intersection(poly2).area / poly1.union(poly2).area
    return 0.


def _mask_iou(mask1: np.ndarray, mask2: np.ndarray) -> float:
    """Computes iou between two binary segmentation masks."""
    return np.sum(mask1 & mask2) / np.sum(mask1 | mask2)


def _remove_opacity_channel(masks: List[np.ndarray]) -> List[np.ndarray]:
    return [mask[:, :, :3] if mask.shape[-1] == 4 else mask for mask in masks]


def _instance_urls_to_binary_mask(urls: List[str],
                                  color: Tuple[int, int, int]) -> np.ndarray:
    """Downloads segmentation masks and turns the image into a binary mask."""
    masks = _remove_opacity_channel([url_to_numpy(url) for url in urls])
    return np.sum([np.all(mask == color, axis=-1) for mask in masks],
                  axis=0) > 0
