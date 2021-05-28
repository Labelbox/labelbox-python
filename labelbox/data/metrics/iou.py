from labelbox.data.metrics.preprocess import create_schema_lookup, to_shapely_polys, url_to_numpy
from typing import Dict, Any, List, Optional
from shapely.geometry import Polygon
from itertools import product
import numpy as np

ALL_TOOL_TYPES = {'bbox', 'polygon', 'line', 'point', 'segmentation', 'answer', 'answers'}

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

def classification_iou(prediction, label) -> float:
    # prediction and label must have the same feature schema (and therefore have the same keys..)
    if len(prediction) != len(label) != 1 and not ('answers' in prediction and 'answers' in label) and not ('answer' in prediction and 'answer' in label):
        return 0.

    if len(prediction) == 1:
        prediction = prediction[0]
    if len(label) == 1:
        label = label[0]

    if 'answer' in prediction:
        if isinstance(prediction['answer'], str):
            # Free form text
            return float(prediction['answer'] == label['answer'])
        # radio
        return float(prediction['answer']['schemaId'] == label['answer']['schemaId'])
    elif 'answers' in prediction:
        schema_ids_pred = {answer['schemaId'] for answer in prediction['answers']}
        schema_ids_label = {answer['schemaId'] for answer in label['answers']}
        return float( len(schema_ids_label & schema_ids_pred) / len(schema_ids_label | schema_ids_pred))
    else:
        raise ValueError(f"Unexpected subclass. {prediction}")


def vector_iou(predictions: List[Dict[str, Any]], labels: List[Dict[str, Any]],
               tool: str, include_subclasses = True) -> float:
    agreements = [(feature_a['uuid'], feature_a.get('classifications',[]), feature_b['featureId'], feature_b.get('classifications',[]),
                   _polygon_iou(polygon_a, polygon_b))
                  for (feature_a, polygon_a), (feature_b, polygon_b) in product(
                      zip(predictions, to_shapely_polys(predictions, tool)),
                      zip(labels, to_shapely_polys(labels, tool)))
                  if polygon_a is not None and polygon_b is not None]

    agreements = [(feature_a, subclasses_a, feature_b, subclasses_b, agreement)
                  for feature_a, subclasses_a, feature_b, subclasses_b, agreement in agreements]
    agreements.sort(key=lambda triplet: triplet[4], reverse=True)
    solution_agreements = []
    solution_features = set()
    all_features = set()
    for a, a_classification, b, b_classification, agreement in agreements:
        all_features.update({a, b})
        if a not in solution_features and b not in solution_features:
            solution_features.update({a, b})
            if include_subclasses:
                a_classification = create_schema_lookup(a_classification)
                b_classification = create_schema_lookup(b_classification)
                feature_schemas = set(a_classification.keys()).union(set(b_classification.keys()))
                classification_iou = [feature_miou(a_classification[feature_schema],b_classification[feature_schema]) for feature_schema in feature_schemas]
                classification_iou = [x for x in classification_iou if x is not None]
                classification_iou = agreement if not len(classification_iou) else np.mean(classification_iou)
                # Weighted average of prediction and agreement. Or do we want it to be wrong?
                solution_agreements.append( (agreement + classification_iou) / 2.)
            else:
                solution_agreements.append(agreement)

    # Add zeros for unmatched Features
    solution_agreements.extend([0.0] *
                               (len(all_features) - len(solution_features)))
    return np.mean(solution_agreements)

def feature_miou(predictions: List[Dict[str, Any]],
                 labels: List[Dict[str, Any]], include_subclasses = True) -> Optional[float]:
    if len(predictions):
        keys = predictions[0]
    elif len(labels):
        # No existing predictions but existing labels means no matches.
        return 0.0
    else:
        # Ignore examples that do not have any labels or predictions
        return None

    tool = (set(keys) & ALL_TOOL_TYPES or {"segmentation"}).pop()
    if tool == 'segmentation':
        return mask_iou(predictions, labels)
    elif tool in {'polygon', 'bbox', 'line', 'point'}:
        return vector_iou(predictions, labels, tool, include_subclasses=include_subclasses)
    elif tool in {'answer', 'answers'}:
        return classification_iou(predictions, labels)
    else:
        raise ValueError(
            f"Unexpected annotation found. Must be one of {ALL_TOOL_TYPES}")

def datarow_miou(label_content: List[Dict[str, Any]],
                 ndjsons: List[Dict[str, Any]], include_classifications = True, include_subclasses = True) -> float:
    """
    label_content is the bulk_export['Label']

    label: Label in the bulk export format
    ndjson: All ndjsons that have the same datarow as the label (must be a polygon, mask, or box ndjson).

    # We are assuming that these are all valid payloads ..
    """

    if include_classifications:
        label_content = label_content['objects'] + label_content['classifications']
    else:
        label_content = label_content['objects']

    labels = create_schema_lookup(label_content)
    predictions = create_schema_lookup(ndjsons)
    feature_schemas = set(predictions.keys()).union(set(labels.keys()))
    # TODO: Do we need to weight this by the number of examples in a class?
    # What does B&C do?
    ious = []
    # This weights each class equally so rare classes will have a larger impact on the iou
    for feature_schema in feature_schemas:
        ious.append(
            feature_miou(predictions[feature_schema], labels[feature_schema], include_subclasses=  include_subclasses))
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
