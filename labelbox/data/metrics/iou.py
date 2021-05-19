from labelbox.data.metrics.preprocess import lookup_by_schema, to_shapely_polys, url_to_numpy
from typing import Dict, Any, List
from shapely.geometry import Polygon
from itertools import product
import numpy as np

SUPPORTED_TYPES = {'segmentation', 'polygon', 'bbox'}
ALL_TYPES = {'bbox', 'polygon', 'line', 'point', 'segmentation'}


def polygon_iou(p1: Polygon, p2: Polygon) -> float:
    if p1.intersects(p2):
        return p1.intersection(p2).area / p1.union(p2).area
    return 0.


def mask_iou(tool_pred, tool_label):
    """
    Mask iou is performed at the class level and not the instance level.
    """
    # This is kind of inefficient. The mask exists locally for them to upload it.
    # RLE data would be convenient here.
    assert len(tool_label) == 1

    # There will only ever be one mask label per class
    label = url_to_numpy(tool_label[0]['instanceURI'])
    pred_masks = [url_to_numpy(x['instanceURI']) for x in tool_pred]

    label = np.sum(label, axis=-1) > 0
    pred_mask = np.sum(pred_masks, axis=(0, 3)) > 0

    assert label.shape == pred_mask.shape
    return np.sum(label & pred_mask) / np.sum(label | pred_mask)


def vector_iou(tool_pred, tool_label, keys):
    agreements = [(feature_a['uuid'], feature_b['featureId'],
                   polygon_iou(polygon_a, polygon_b))
                  for (feature_a, polygon_a), (feature_b, polygon_b) in product(
                      zip(tool_pred, to_shapely_polys(tool_pred, keys)),
                      zip(tool_label, to_shapely_polys(tool_label, keys)))
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


def feature_miou(predictions, labels):
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


def datarow_miou(label_content: Dict[str, Any],
                 ndjsons: List[Dict[str, Any]]) -> float:
    """
    label_content is the bulk_export['Label']['objects']

    label: Label in the bulk export format
    ndjson: All ndjsons that have the same datarow as the label (must be a polygon, mask, or box ndjson).

    # We are assuming that these are all valid payloads ..
    """
    labels = lookup_by_schema(label_content)
    predictions = lookup_by_schema(ndjsons)
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
