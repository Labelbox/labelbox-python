import json
import datetime as dt
import logging
from shapely import wkt
from shapely.geometry import Polygon
import requests
from PIL import Image

from labelbox2pascal import UnknownFormatError


def from_json(labeled_data, coco_output, label_format='WKT'):
    # read labelbox JSON output
    with open(labeled_data, 'r') as f:
        label_data = json.loads(f.read())

    # setup COCO dataset container and info
    coco = make_coco_metadata(label_data[0]['Project Name'], label_data[0]['Created By'],)

    for data in label_data:
        # Download and get image name
        try:
            add_label(coco, data['ID'], data['Labeled Data'], data['Label'], label_format)
        except requests.exceptions.MissingSchema as e:
            logging.exception(('"Labeled Data" field must be a URL. '
                              'Support for local files coming soon'))
            continue
        except requests.exceptions.ConnectionError as e:
            logging.exception('Failed to fetch image from {}'
                              .format(data['Labeled Data']))
            continue

    with open(coco_output, 'w+') as f:
        f.write(json.dumps(coco))

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

def add_label(coco, label_id, image_url, labels, label_format):
    "Incrementally updates COCO export data structure with a new label."
    response = requests.get(image_url, stream=True)
    response.raw.decode_content = True
    im = Image.open(response.raw)
    width, height = im.size

    image = {
        "id": label_id,
        "width": width,
        "height": height,
        "file_name": image_url,
        "license": None,
        "flickr_url": image_url,
        "coco_url": image_url,
        "date_captured": None,
    }

    coco['images'].append(image)

    # remove classification labels (Skip, etc...)
    if not callable(getattr(labels, 'keys', None)):
        return

    # convert label to COCO Polygon format
    for category_name, label_data in labels.items():
        try:
            # check if label category exists in 'categories' field
            category_id = [c['id'] for c in coco['categories'] if c['supercategory'] == category_name][0]
        except IndexError:
            category_id = len(coco['categories']) + 1
            category = {
                'supercategory': category_name,
                'id': category_id,
                'name': category_name
            }
            coco['categories'].append(category)

        if label_format == 'WKT':
            if type(label_data) is list: # V3
                polygons = map(lambda x: wkt.loads(x['geometry']), label_data)
            else: # V2
                polygons = wkt.loads(label_data)
        elif label_format == 'XY':
            polygons = []
            for xy_list in label_data:
                if 'geometry' in xy_list: # V3
                    xy_list = xy_list['geometry']
                    assert type(xy_list) is list, 'Expected list in "geometry" key but got {}'.format(xy_list) # V2 and V3
                else: # V2, or non-list
                    if type(xy_list) is not list or len(xy_list) == 0 or 'x' not in xy_list[0]: # skip non xy lists
                        continue

                polygons.append(Polygon(map(lambda p: (p['x'], p['y']), xy_list)))
        else:
            e = UnknownFormatError(label_format=label_format)
            logging.exception(e.message)
            raise e

        for polygon in polygons:
            segmentation = []
            for x, y in polygon.exterior.coords:
                segmentation.extend([x, height - y])

            annotation = {
                "id": len(coco['annotations']) + 1,
                "image_id": label_id,
                "category_id": category_id,
                "segmentation": [segmentation],
                "area": polygon.area,  # float
                "bbox": [polygon.bounds[0], polygon.bounds[1],
                            polygon.bounds[2] - polygon.bounds[0],
                            polygon.bounds[3] - polygon.bounds[1]],
                "iscrowd": 0
            }

            coco['annotations'].append(annotation)

