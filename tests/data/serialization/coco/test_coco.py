import json
from pathlib import Path

from labelbox.data.serialization.coco import COCOConverter

COCO_ASSETS_DIR = "tests/data/assets/coco"


def run_instances():
    instance_json = json.load(open(Path(COCO_ASSETS_DIR, 'instances.json')))
    res = COCOConverter.deserialize_instances(instance_json,
                                              Path(COCO_ASSETS_DIR, 'images'))
    back = COCOConverter.serialize_instances(
        res,
        Path('tmp/images_instances'),
    )


def test_rle_objects():
    rle_json = json.load(open(Path(COCO_ASSETS_DIR, 'rle.json')))
    res = COCOConverter.deserialize_instances(rle_json,
                                              Path(COCO_ASSETS_DIR, 'images'))
    back = COCOConverter.serialize_instances(res, Path('/tmp/images_rle'))


def test_panoptic():
    panoptic_json = json.load(open(Path(COCO_ASSETS_DIR, 'panoptic.json')))
    image_dir, mask_dir = [
        Path(COCO_ASSETS_DIR, dir_name) for dir_name in ['images', 'masks']
    ]
    res = COCOConverter.deserialize_panoptic(panoptic_json, image_dir, mask_dir)
    back = COCOConverter.serialize_panoptic(res, Path('/tmp/images_panoptic'),
                                            Path('/tmp/masks_panoptic'))
