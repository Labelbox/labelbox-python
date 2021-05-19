from typing import List, Dict, Any
from collections import defaultdict
from shapely.geometry import Polygon, box
import numpy as np
from PIL import Image
import requests


def create_schema_lookup(rows: Dict[str, Any]) -> Dict[str, List[Any]]:
    data = defaultdict(list)
    for row in rows:
        data[row['schemaId']].append(row)
    return data


def url_to_numpy(mask_url: str) -> np.ndarray:
    return np.array(Image.open(requests.get(mask_url).raw))


def _bbox_to_shapely_poly(bbox: Dict[str, float]) -> Polygon:
    return box(bbox['left'], bbox['top'], bbox['left'] + bbox['width'],
               bbox['top'] + bbox['height'])


def _poly_to_shapely_poly(poly: List[Dict[str, float]]) -> Polygon:
    return Polygon([[pt['x'], pt['y']] for pt in poly])


def to_shapely_polys(tool: List[Dict[str, Any]],
                     keys: List[str]) -> List[Polygon]:
    if 'polygon' in keys:
        return [_poly_to_shapely_poly(poly['polygon']) for poly in tool]
    else:
        return [_bbox_to_shapely_poly(bbox['bbox']) for bbox in tool]
