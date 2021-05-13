from typing import Dict, Any, List
from labelbox import Label
from shapely.geometry import Polygon, polygon
from itertools import product
from collections import defaultdict
import numpy as np
from io import BytesIO
from PIL import Image
import requests

SUPPORTED_TYPES = {'mask', 'polygon', 'bbox'}


def polygon_iou(p1: Polygon, p2: Polygon) -> float:
    if p1.intersects(p2):
        return p1.intersection(p2).area / p1.union(p2).area
    return 0.

def mask_iou(m1 : np.bool, m2 : np.bool) -> float:
    """
    Mask iou is performed at the class level and not the instance level.

    """
    return np.sum(m1 & m2) / np.sum( m1 | m2 )


def datarow_miou(label_content: Dict[str, Any], ndjsons : List[Dict[str, Any]]) -> float:
    """
    label: Label in the bulk export format
    ndjson: All ndjsons that have the same datarow as the label (must be a polygon, mask, or box ndjson).

    # We are assuming that these are all valid payloads ..
    """
    labels = defaultdict(list)
    predictions = defaultdict(list)
    for annot in label_content:
        labels[annot['schemaId']].append(annot)

    for pred in ndjsons:
        predictions[pred['featureSchema']['Id']].append(pred)

    feature_schemas = set(pred.keys()).union(set(labels.keys()))
    # TODO: Do we need to weight this by the number of examples in a class?
    # What does B&C do?
    ious = [] 
    for feature_schema in feature_schemas:
        if len(predictions[feature_schema]):
            keys = predictions[feature_schema][0]
        elif len(labels[feature_schema]):
            # No existing predictions but existing labels means no matches.
            ious.append(0.0)
        else:
            continue # I guess we just ignore these

        if 'mask' in keys:
            # This is kind of inefficient. The mask exists locally for them to upload it.
            assert len(labels[feature_schema]) == 1
            label = np.array(Image.open(BytesIO(requests.get(labels[feature_schema][0]['mask']))))
            label = np.sum(label, axis = -1) > 0
            pred_masks = [np.array(Image.open(BytesIO(requests.get(x['mask'])))) for x in predictions[feature_schema]]
            pred_mask = np.sum(pred_masks, axis = (0, 3)) > 0
            assert label.shape == pred_mask.shape
            ious.append(mask_iou(label, pred_mask))
        elif 'polygon' in keys or 'bbox' in keys:
            if 'polygon' in keys:
                key = 'polygon'
            else:
                key = 'bbox'
            pred_geoms = [Polygon([[pt['x'], pt['y']] for pt in x[key]]) for x in predictions[feature_schema]]
            label_geoms = [Polygon([[pt['x'], pt['y']] for pt in x[key]]) for x in labels[feature_schema]]

            agreements = [(feature_a, feature_b, polygon_iou(polygon_a, polygon_b))
            for (feature_a, polygon_a), (feature_b, polygon_b)
            in product(zip(predictions[feature_schema], pred_geoms),
                                 zip(labels[feature_schema], label_geoms))
            if polygon_a is not None and polygon_b is not None]
            
            agreements = [(feature_a["feature_id"], feature_b["feature_id"], agreement) for feature_a, feature_b, agreement in agreements]
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
            solution_agreements.extend(
                [0.0] * (len(all_features) - len(solution_features)))
            ious.append(np.mean(solution_agreements))
        else:
            raise ValueError(f"Unexpected annotation found. Must be one of {SUPPORTED_TYPES}")


        




    



    


