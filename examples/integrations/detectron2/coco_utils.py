from concurrent.futures import ThreadPoolExecutor, as_completed
import functools
import random
import json
import os

import numpy as np
from PIL import Image
from tqdm import tqdm
import cv2
from detectron2.utils.visualizer import Visualizer
from panopticapi.utils import rgb2id


def get_annotations(images, all_annotations):
    image_lookup = {image['id'] for image in images}
    return [
        annot for annot in all_annotations if annot['image_id'] in image_lookup
    ]


def partition_indices(total_n, splits):

    if splits is None:
        raise ValueError("")

    if sum(splits) != 1.:
        raise ValueError(f"Found {sum(splits)}. Expected 1.")

    splits = np.cumsum(splits)
    for idx in range(len((splits))):
        start = 0 if idx == 0 else int(total_n * splits[idx - 1])
        end = int(splits[idx] * total_n)
        yield start, end


def partition_coco(coco_instance_data, coco_panoptic_data=None, splits=None):
    images = coco_instance_data['images']
    n_classes = len(
        {category['id'] for category in coco_instance_data['categories']})
    random.shuffle(images)
    partitions = []
    for start, end in partition_indices(len(images), splits):
        partition = {
            'instance':
                dict(categories=coco_instance_data['categories'],
                     images=images[start:end],
                     annotations=get_annotations(
                         images[start:end], coco_instance_data['annotations']))
        }
        if coco_panoptic_data is not None:
            partition['panoptic'] = dict(
                categories=coco_panoptic_data['categories'],
                images=images[start:end],
                annotations=get_annotations(images[start:end],
                                            coco_panoptic_data['annotations']))
        partitions.append(partition)
    return partitions


def visualize_object_inferences(metadata_catalog,
                                coco_examples,
                                predictor,
                                scale=1.0,
                                max_images=5,
                                resize_dims=(768, 512)):
    images = []
    for idx, example in enumerate(coco_examples):
        if idx > max_images:
            break
        im = cv2.imread(example['file_name'])
        outputs = predictor(im)
        v = Visualizer(im[:, :, ::-1], metadata_catalog, scale=scale)
        out = v.draw_instance_predictions(outputs["instances"].to("cpu"))
        images.append(cv2.resize(out.get_image()[:, :, ::-1], resize_dims))
    return Image.fromarray(np.vstack(images))


def visualize_coco_examples(metadata_catalog,
                            object_examples,
                            panoptic_examples=None,
                            scale=1.0,
                            max_images=5,
                            resize_dims=(768, 512)):
    if panoptic_examples is not None:
        lookup = {d['file_name']: d for d in panoptic_examples}

    images = []
    for idx, example in enumerate(object_examples):
        if idx > max_images:
            break
        im = cv2.imread(example['file_name'])
        v = Visualizer(im[:, :, ::-1], metadata_catalog, scale=scale)
        out = v.draw_dataset_dict(example)
        if panoptic_examples is not None:
            example_panoptic = lookup.get(example['file_name'])
            if example_panoptic is not None:
                out = v.draw_dataset_dict(example_panoptic)
        images.append(cv2.resize(out.get_image(), resize_dims))
    return Image.fromarray(np.vstack(images))


def _process_panoptic_to_semantic(input_panoptic, output_semantic, segments,
                                  id_map):
    panoptic = np.asarray(Image.open(input_panoptic), dtype=np.uint32)
    panoptic = rgb2id(panoptic)

    output = np.zeros_like(panoptic, dtype=np.uint8)
    for seg in segments:
        cat_id = seg["category_id"]
        new_cat_id = id_map[cat_id]
        output[panoptic == seg["id"]] = new_cat_id
    Image.fromarray(output).save(output_semantic)


def separate_coco_semantic_from_panoptic(panoptic_json, panoptic_root,
                                         sem_seg_root, categories):
    """
    Create semantic segmentation annotations from panoptic segmentation
    annotations, to be used by PanopticFPN.

    It maps all thing categories to class 0, and maps all unlabeled pixels to class 255.
    It maps all stuff categories to contiguous ids starting from 1.

    Args:
        panoptic_json (str): path to the panoptic json file, in COCO's format.
        panoptic_root (str): a directory with panoptic annotation files, in COCO's format.
        sem_seg_root (str): a directory to output semantic annotation files
        categories (list[dict]): category metadata. Each dict needs to have:
            "id": corresponds to the "category_id" in the json annotations
            "isthing": 0 or 1
    """
    os.makedirs(sem_seg_root, exist_ok=True)

    stuff_ids = [k["id"] for k in categories if k["isthing"] == 0]
    thing_ids = [k["id"] for k in categories if k["isthing"] == 1]
    id_map = {}  # map from category id to id in the output semantic annotation
    assert len(stuff_ids) <= 254
    for i, stuff_id in enumerate(stuff_ids):
        id_map[stuff_id] = i + 1
    for thing_id in thing_ids:
        id_map[thing_id] = 0
    id_map[0] = 255

    with open(panoptic_json) as f:
        obj = json.load(f)

    def iter_annotations():
        for anno in obj["annotations"]:
            file_name = anno["file_name"]
            segments = anno["segments_info"]
            input = os.path.join(panoptic_root, file_name)
            output = os.path.join(sem_seg_root, file_name)
            yield input, output, segments

    fn = functools.partial(_process_panoptic_to_semantic, id_map=id_map)
    futures = []
    with ThreadPoolExecutor(max_workers=12) as executor:
        for args in iter_annotations():
            futures.append(executor.submit(fn, *args))
        for _ in tqdm(as_completed(futures)):
            _.result()
