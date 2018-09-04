import json
import datetime as dt
import logging
from shapely import wkt
import requests
from PIL import Image


def from_json(labeled_data, coco_output):
    # read labelbox JSON output
    with open(labeled_data, 'r') as f:
        label_data = json.loads(f.read())

    # setup COCO dataset container and info
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
        'description': label_data[0]['Project Name'],
        'contributor': label_data[0]['Created By'],
        'url': 'labelbox.com',
        'date_created': dt.datetime.now(dt.timezone.utc).isoformat()
    }

    for data in label_data:
        # Download and get image name
        try:
            response = requests.get(data['Labeled Data'], stream=True)
        except requests.exceptions.MissingSchema as e:
            logging.exception(('"Labeled Data" field must be a URL. '
                              'Support for local files coming soon'))
            continue
        except requests.exceptions.ConnectionError as e:
            logging.exception('Failed to fetch image from {}'
                              .format(data['Labeled Data']))
            continue

        response.raw.decode_content = True
        im = Image.open(response.raw)
        width, height = im.size

        image = {
            "id": data['ID'],
            "width": width,
            "height": height,
            "file_name": data['Labeled Data'],
            "license": None,
            "flickr_url": data['Labeled Data'],
            "coco_url": data['Labeled Data'],
            "date_captured": None,
        }

        coco['images'].append(image)

        # remove classification labels (Skip, etc...)
        labels = data['Label']
        if not callable(getattr(labels, 'keys', None)):
            continue

        # convert label to COCO Polygon format
        for category_name, wkt_data in labels.items():
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

            if type(wkt_data) is list:
                polygons = map(lambda x: wkt.loads(x['geometry']), wkt_data)
            else:
                polygons = wkt.loads(wkt_data)

            for polygon in polygons:
                segmentation = []
                for x, y in polygon.exterior.coords:
                    segmentation.extend([x, height - y])

                annotation = {
                    "id": len(coco['annotations']) + 1,
                    "image_id": data['ID'],
                    "category_id": category_id,
                    "segmentation": [segmentation],
                    "area": polygon.area,  # float
                    "bbox": [polygon.bounds[0], polygon.bounds[1],
                             polygon.bounds[2] - polygon.bounds[0],
                             polygon.bounds[3] - polygon.bounds[1]],
                    "iscrowd": 0
                }

                coco['annotations'].append(annotation)

    with open(coco_output, 'w+') as f:
        f.write(json.dumps(coco))
