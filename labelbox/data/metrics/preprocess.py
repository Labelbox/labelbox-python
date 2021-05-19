from typing import DefaultDict
from shapely.geometry import Polygon, box
import numpy as np
from PIL import Image
import requests


def bbox_to_shapely_poly(bbox):
    return box(bbox['left'], bbox['top'], bbox['left'] + bbox['width'],
               bbox['top'] + bbox['height'])


def poly_to_shapely_poly(poly):
    return Polygon([[pt['x'], pt['y']] for pt in poly])


def to_shapely_polys(tool, keys):
    if 'polygon' in keys:
        return [poly_to_shapely_poly(poly['polygon']) for poly in tool]
    else:
        return [bbox_to_shapely_poly(bbox['bbox']) for bbox in tool]


def lookup_by_schema(rows):
    data = DefaultDict(list)
    for row in rows:
        data[row['schemaId']].append(row)
    return data


def url_to_numpy(mask_url):
    return np.array(Image.open(requests.get(mask_url).raw))
