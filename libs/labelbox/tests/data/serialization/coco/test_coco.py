import json
from pathlib import Path

from labelbox.data.serialization.coco import COCOConverter

COCO_ASSETS_DIR = "tests/data/assets/coco"


def run_instances(tmpdir):
    instance_json = json.load(open(Path(COCO_ASSETS_DIR, "instances.json")))
    res = COCOConverter.deserialize_instances(
        instance_json, Path(COCO_ASSETS_DIR, "images")
    )
    back = COCOConverter.serialize_instances(
        res,
        Path(tmpdir),
    )


def test_rle_objects(tmpdir):
    rle_json = json.load(open(Path(COCO_ASSETS_DIR, "rle.json")))
    res = COCOConverter.deserialize_instances(
        rle_json, Path(COCO_ASSETS_DIR, "images")
    )
    back = COCOConverter.serialize_instances(res, tmpdir)


def test_panoptic(tmpdir):
    panoptic_json = json.load(open(Path(COCO_ASSETS_DIR, "panoptic.json")))
    image_dir, mask_dir = [
        Path(COCO_ASSETS_DIR, dir_name) for dir_name in ["images", "masks"]
    ]
    res = COCOConverter.deserialize_panoptic(panoptic_json, image_dir, mask_dir)
    back = COCOConverter.serialize_panoptic(
        res,
        Path(f"/{tmpdir}/images_panoptic"),
        Path(f"/{tmpdir}/masks_panoptic"),
    )
