from typing import List, Dict, Any
from collections import defaultdict
from shapely.geometry import Polygon, Point, LineString, box
import numpy as np
from PIL import Image
import requests
from io import BytesIO


def create_schema_lookup(rows: Dict[str, Any]) -> Dict[str, List[Any]]:
    data = defaultdict(list)
    for row in rows:
        data[row['schemaId']].append(row)
    return data


def url_to_numpy(mask_url: str) -> np.ndarray:
    return np.array(Image.open(BytesIO(requests.get(mask_url).content)))

def _bbox_to_shapely_poly(bbox: Dict[str, float]) -> Polygon:
    return box(bbox['left'], bbox['top'], bbox['left'] + bbox['width'],
               bbox['top'] + bbox['height'])


def _poly_to_shapely_poly(poly: List[Dict[str, float]]) -> Polygon:
    return Polygon([[pt['x'], pt['y']] for pt in poly])

def _poly_to_shapely_poly(poly: List[Dict[str, float]]) -> Polygon:
    return Polygon([[pt['x'], pt['y']] for pt in poly])

def _line_to_shapely_poly(line: List[Dict[str, float]], buffer: int = 70) -> Polygon:
    return LineString([[pt['x'], pt['y']] for pt in line]).buffer(buffer)

def _point_to_shapely_poly(point: List[Dict[str, float]], buffer: int = 70) -> Polygon:
    return Point([point['x'], point['y']]).buffer(buffer)

def to_shapely_polys(tool: List[Dict[str, Any]],
                     tool_name: str) -> List[Polygon]:
    if tool_name == 'polygon':
        return [_poly_to_shapely_poly(poly[tool_name]) for poly in tool]
    elif tool_name == 'bbox':
        return [_bbox_to_shapely_poly(poly[tool_name]) for poly in tool]
    elif tool_name == 'point':
        return [_point_to_shapely_poly(point[tool_name]) for point in tool]
    elif tool_name == 'line':
        return [_line_to_shapely_poly(point[tool_name]) for point in tool]
    else:
        raise ValueError(f"Unexpected tool type found {tool_name}")


