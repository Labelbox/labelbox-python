from labelbox.data.metrics.preprocess import create_schema_lookup, to_shapely_polys, url_to_numpy
from typing import Dict, Any, List, Optional
from shapely.geometry import Polygon
from itertools import product
import numpy as np

SUPPORTED_TYPES = {'segmentation', 'polygon', 'bbox'}
ALL_TYPES = {'bbox', 'polygon', 'line', 'point', 'segmentation'}


def mask_iou(predictions: List[Dict[str, Any]],
             labels: List[Dict[str, Any]]) -> float:
    """
    Mask iou is performed at the class level and not the instance level.
    """
    # This is inefficient. The mask exists locally for them to upload it.
    # RLE data would be convenient here.
    # There will only ever be one mask label per class
    label_mask = _instance_urls_to_binary_mask(
        [pred['instanceURI'] for pred in predictions])
    pred_mask = _instance_urls_to_binary_mask(
        [label['instanceURI'] for label in labels])
    assert label_mask.shape == pred_mask.shape
    return _mask_iou(label_mask, pred_mask)


def vector_iou(predictions: List[Dict[str, Any]], labels: List[Dict[str, Any]],
               keys: Dict[str, Any]) -> float:
    agreements = [(feature_a['uuid'], feature_b['featureId'],
                   _polygon_iou(polygon_a, polygon_b))
                  for (feature_a, polygon_a), (feature_b, polygon_b) in product(
                      zip(predictions, to_shapely_polys(predictions, keys)),
                      zip(labels, to_shapely_polys(labels, keys)))
                  if polygon_a is not None and polygon_b is not None]

    agreements = [(feature_a, feature_b, agreement)
                  for feature_a, feature_b, agreement in agreements]
    agreements.sort(key=lambda triplet: triplet[2], reverse=True)
    solution_agreements = []
    solution_features = set()
    all_features = set()
    for a, b, agreement in agreements:
        all_features.update({a, b})
        if a not in solution_features and b not in solution_features:
            solution_features.update({a, b})
            solution_agreements.append(agreement)

    # Add zeros for unmatched Features
    solution_agreements.extend([0.0] *
                               (len(all_features) - len(solution_features)))
    return np.mean(solution_agreements)


def feature_miou(predictions: List[Dict[str, Any]],
                 labels: List[Dict[str, Any]]) -> Optional[float]:
    if len(predictions):
        keys = predictions[0]
    elif len(labels):
        # No existing predictions but existing labels means no matches.
        return 0.0
    else:
        # Ignore examples that do not have any labels or predictions
        return None

    tool = (set(keys) & ALL_TYPES or {"segmentation"}).pop()
    if tool == 'segmentation':
        return mask_iou(predictions, labels)
    elif tool in {'polygon', 'bbox'}:
        return vector_iou(predictions, labels, keys)
    else:
        raise ValueError(
            f"Unexpected annotation found. Must be one of {SUPPORTED_TYPES}")


def datarow_miou(label_content: List[Dict[str, Any]],
                 ndjsons: List[Dict[str, Any]]) -> float:
    """
    label_content is the bulk_export['Label']['objects']

    label: Label in the bulk export format
    ndjson: All ndjsons that have the same datarow as the label (must be a polygon, mask, or box ndjson).

    # We are assuming that these are all valid payloads ..
    """
    labels = create_schema_lookup(label_content)
    predictions = create_schema_lookup(ndjsons)
    feature_schemas = set(predictions.keys()).union(set(labels.keys()))
    # TODO: Do we need to weight this by the number of examples in a class?
    # What does B&C do?
    ious = []
    # This weights each class equally so rare classes will have a larger impact on the iou
    for feature_schema in feature_schemas:
        ious.append(
            feature_miou(predictions[feature_schema], labels[feature_schema]))
    ious = [iou for iou in ious if iou is not None]
    if not ious:
        # TODO: Figure out the behavior we want for this.
        raise ValueError("No predictions or labels found for this example....")
    return np.mean(ious)


def _polygon_iou(poly1: Polygon, poly2: Polygon) -> float:
    if poly1.intersects(poly2):
        return poly1.intersection(poly2).area / poly1.union(poly2).area
    return 0.


def _mask_iou(mask1: np.ndarray, mask2: np.ndarray) -> float:
    return np.sum(mask1 & mask2) / np.sum(mask1 | mask2)


def _instance_urls_to_binary_mask(urls: List[str]) -> np.ndarray:
    masks = [url_to_numpy(url) for url in urls]
    return np.sum(masks, axis=(0, 3)) > 0
