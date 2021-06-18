# type: ignore
from typing import Dict, Any, List, Optional, Tuple, Union
from shapely.geometry import Polygon
from itertools import product
import numpy as np

from labelbox.data.metrics.preprocess import label_to_ndannotation
from labelbox.schema.bulk_import_request import (NDAnnotation, NDChecklist,
                                                 NDClassification, NDTool,
                                                 NDMask, NDPoint, NDPolygon,
                                                 NDPolyline, NDRadio, NDText,
                                                 NDRectangle)
from labelbox.data.metrics.preprocess import (create_schema_lookup,
                                              url_to_numpy)

VectorTool = Union[NDPoint, NDRectangle, NDPolyline, NDPolygon]
ClassificationTool = Union[NDText, NDRadio, NDChecklist]


def mask_miou(predictions: List[NDMask], labels: List[NDMask]) -> float:
    """
    Creates prediction and label binary mask for all features with the same feature schema id.

    Args:
        predictions: List of masks objects
        labels: List of masks objects
    Returns:
        float indicating iou score
    """

    colors_pred = {tuple(pred.mask['colorRGB']) for pred in predictions}
    colors_label = {tuple(label.mask['colorRGB']) for label in labels}
    error_msg = "segmentation {} should all have the same color. Found {}"
    if len(colors_pred) > 1:
        raise ValueError(error_msg.format("predictions", colors_pred))
    elif len(colors_label) > 1:
        raise ValueError(error_msg.format("labels", colors_label))

    pred_mask = _instance_urls_to_binary_mask(
        [pred.mask['instanceURI'] for pred in predictions], colors_pred.pop())
    label_mask = _instance_urls_to_binary_mask(
        [label.mask['instanceURI'] for label in labels], colors_label.pop())
    assert label_mask.shape == pred_mask.shape
    return _mask_iou(label_mask, pred_mask)


def classification_miou(predictions: List[ClassificationTool],
                        labels: List[ClassificationTool]) -> float:
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

    if isinstance(prediction, NDText):
        return float(prediction.answer == label.answer)
    elif isinstance(prediction, NDRadio):
        return float(prediction.answer.schemaId == label.answer.schemaId)
    elif isinstance(prediction, NDChecklist):
        schema_ids_pred = {answer.schemaId for answer in prediction.answers}
        schema_ids_label = {answer.schemaId for answer in label.answers}
        return float(
            len(schema_ids_label & schema_ids_pred) /
            len(schema_ids_label | schema_ids_pred))
    else:
        raise ValueError(f"Unexpected subclass. {prediction}")


def subclassification_miou(
        subclass_predictions: List[ClassificationTool],
        subclass_labels: List[ClassificationTool]) -> Optional[float]:
    """

    Computes subclass iou score between two vector tools that were matched.

    Arg:
        subclass_predictions: All subclasses for a particular vector feature inference
        subclass_labels : All subclass labels for a label that matched with the vector feature inference.

    Returns:
        miou across all subclasses.
    """

    subclass_predictions = create_schema_lookup(subclass_predictions)
    subclass_labels = create_schema_lookup(subclass_labels)
    feature_schemas = set(subclass_predictions.keys()).union(
        set(subclass_labels.keys()))
    # There should only be one feature schema per subclass.

    classification_iou = [
        feature_miou(subclass_predictions[feature_schema],
                     subclass_labels[feature_schema])
        for feature_schema in feature_schemas
    ]
    classification_iou = [x for x in classification_iou if x is not None]
    return None if not len(classification_iou) else np.mean(classification_iou)


def vector_miou(predictions: List[VectorTool], labels: List[VectorTool],
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


def feature_miou(predictions: List[NDAnnotation],
                 labels: List[NDAnnotation],
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

    tool_types = {type(annot) for annot in predictions
                 }.union({type(annot) for annot in labels})

    if len(tool_types) > 1:
        raise ValueError(
            "feature_miou predictions and annotations should all be of the same type"
        )

    tool_type = tool_types.pop()
    if tool_type == NDMask:
        return mask_miou(predictions, labels)
    elif tool_type in NDTool.get_union_types():
        return vector_miou(predictions,
                           labels,
                           include_subclasses=include_subclasses)
    elif tool_type in NDClassification.get_union_types():
        return classification_miou(predictions, labels)
    else:
        raise ValueError(f"Unexpected annotation found. Found {tool_type}")


def datarow_miou(label_content: List[Dict[str, Any]],
                 ndjsons: List[Dict[str, Any]],
                 include_classifications=True,
                 include_subclasses=True) -> float:
    """

    Args:
        label_content : one row from the bulk label export - `project.export_labels()`
        ndjsons: Model predictions in the ndjson format specified here (https://docs.labelbox.com/data-model/en/index-en#annotations)
        include_classifications: Whether or not to factor top level classifications into the iou score.
        include_subclassifications: Whether or not to factor in subclassifications into the iou score
    Returns:
        float indicating the iou score for this data row.

    """

    predictions, labels, feature_schemas = _preprocess_args(
        label_content, ndjsons, include_classifications)

    ious = [
        feature_miou(predictions[feature_schema],
                     labels[feature_schema],
                     include_subclasses=include_subclasses)
        for feature_schema in feature_schemas
    ]
    ious = [iou for iou in ious if iou is not None]
    if not ious:
        return None
    return np.mean(ious)


def _preprocess_args(
    label_content: List[Dict[str, Any]],
    ndjsons: List[Dict[str, Any]],
    include_classifications=True
) -> Tuple[Dict[str, List[NDAnnotation]], Dict[str, List[NDAnnotation]],
           List[str]]:
    """

    This function takes in the raw json payloads, validates, and converts to python objects.
    In the future datarow_miou will directly take the objects as args.

    Args:
        label_content : one row from the bulk label export - `project.export_labels()`
        ndjsons: Model predictions in the ndjson format specified here (https://docs.labelbox.com/data-model/en/index-en#annotations)
    Returns a tuple containing:
        - a dict for looking up a list of predictions by feature schema id
        - a dict for looking up a list of labels by feature schema id
        - a list of a all feature schema ids

    """
    labels = label_content['Label'].get('objects')
    if include_classifications:
        labels += label_content['Label'].get('classifications')

    predictions = [NDAnnotation(**pred.copy()) for pred in ndjsons]

    unique_datarows = {pred.dataRow.id for pred in predictions}
    if len(unique_datarows):
        # Empty set of annotations is valid (if labels exist but no inferences then iou will be 0.)
        if unique_datarows != {label_content['DataRow ID']}:
            raise ValueError(
                f"There should only be one datarow passed to the datarow_miou function. Found {unique_datarows}"
            )

    labels = [
        label_to_ndannotation(label, label_content['DataRow ID'])
        for label in labels
    ]

    labels = create_schema_lookup(labels)
    predictions = create_schema_lookup(predictions)

    feature_schemas = set(predictions.keys()).union(set(labels.keys()))
    return predictions, labels, feature_schemas


def _get_vector_pairs(predictions: List[Dict[str, Any]], labels):
    """
    # Get iou score for all pairs of labels and predictions
    """
    return [(prediction, label,
             _polygon_iou(prediction.to_shapely_poly(),
                          label.to_shapely_poly()))
            for prediction, label in product(predictions, labels)]


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
