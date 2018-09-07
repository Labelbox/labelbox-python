"""
Module for converting labelbox.com JSON exports to MS COCO format.
"""

import json
import datetime as dt
import logging
from shapely import wkt
from shapely.geometry import Polygon
import requests
from PIL import Image

from labelbox.exceptions import UnknownFormatError


def from_json(labeled_data, coco_output, label_format='WKT'):
    "Writes labelbox JSON export into MS COCO format."
    # read labelbox JSON output
    with open(labeled_data, 'r') as file_handle:
        label_data = json.loads(file_handle.read())

    # setup COCO dataset container and info
    coco = make_coco_metadata(label_data[0]['Project Name'], label_data[0]['Created By'],)

    for data in label_data:
        # Download and get image name
        try:
            image = {
                "id": data['ID'],
                "file_name": data['Labeled Data'],
                "license": None,
                "flickr_url": data['Labeled Data'],
                "coco_url": data['Labeled Data'],
                "date_captured": None,
            }
            _add_label(coco, image, data['Label'], label_format)
        except requests.exceptions.MissingSchema as exc:
            logging.exception(exc)
            continue
        except requests.exceptions.ConnectionError:
            logging.exception('Failed to fetch image from %s', data['Labeled Data'])
            continue

    with open(coco_output, 'w+') as file_handle:
        file_handle.write(json.dumps(coco))


def make_coco_metadata(project_name, created_by):
    "Initializes COCO export data structure."
    coco = {
        'info': None,
        'images': [],
        'annotations': [],
        'licenses': [],
        'categories': []
    }

    coco['info'] = {
        'year': dt.datetime.now(dt.timezone.utc).year,
        'version': None,
        'description': project_name,
        'contributor': created_by,
        'url': 'labelbox.com',
        'date_created': dt.datetime.now(dt.timezone.utc).isoformat()
    }

    return coco


def _add_label(coco, image, labels, label_format):
    "Incrementally updates COCO export data structure with a new label."
    response = requests.get(image['coco_url'], stream=True)
    response.raw.decode_content = True
    image['width'], image['height'] = Image.open(response.raw).size

    coco['images'].append(image)

    # remove classification labels (Skip, etc...)
    if not callable(getattr(labels, 'keys', None)):
        return

    # convert label to COCO Polygon format
    for category_name, label_data in labels.items():
        try:
            # check if label category exists in 'categories' field
            category_id = [c['id']
                           for c in coco['categories']
                           if c['supercategory'] == category_name][0]
        except IndexError:
            category_id = len(coco['categories']) + 1
            category = {
                'supercategory': category_name,
                'id': category_id,
                'name': category_name
            }
            coco['categories'].append(category)

        polygons = _get_polygons(label_format, label_data)

        for polygon in polygons:
            segmentation = []
            for x_val, y_val in polygon.exterior.coords:
                segmentation.extend([x_val, image['height'] - y_val])

            annotation = {
                "id": len(coco['annotations']) + 1,
                "image_id": image['id'],
                "category_id": category_id,
                "segmentation": [segmentation],
                "area": polygon.area,  # float
                "bbox": [polygon.bounds[0], polygon.bounds[1],
                         polygon.bounds[2] - polygon.bounds[0],
                         polygon.bounds[3] - polygon.bounds[1]],
                "iscrowd": 0
            }

            coco['annotations'].append(annotation)


def _get_polygons(label_format, label_data):
    "Converts segmentation `label: String!` into polygons"
    if label_format == 'WKT':
        if isinstance(label_data, list):  # V3
            polygons = map(lambda x: wkt.loads(x['geometry']), label_data)
        else:  # V2
            polygons = wkt.loads(label_data)
    elif label_format == 'XY':
        polygons = []
        for xy_list in label_data:
            if 'geometry' in xy_list:  # V3
                xy_list = xy_list['geometry']

                # V2 and V3
                assert isinstance(xy_list, list), \
                    'Expected list in "geometry" key but got {}'.format(xy_list)
            else:  # V2, or non-list
                if not isinstance(xy_list, list) or not xy_list or 'x' not in xy_list[0]:
                    # skip non xy lists
                    continue

            polygons.append(Polygon(map(lambda p: (p['x'], p['y']), xy_list)))
    else:
        exc = UnknownFormatError(label_format=label_format)
        logging.exception(exc.message)
        raise exc

    return polygons
