import random
import numpy as np
from PIL import Image
import cv2
from detectron2.utils.visualizer import Visualizer


def get_annotations(images, all_annotations):
    image_lookup = {image['id'] for image in images}
    return [annot for annot in all_annotations if annot['image_id'] in image_lookup]


def partition_indices(total_n, splits):

    if splits is None:
        raise ValueError("")

    if sum(splits) != 1.:
        raise ValueError(f"Found {sum(splits)}. Expected 1.")

    splits = np.cumsum(splits)
    for idx in range(len((splits))):
        start = 0 if idx == 0 else int(total_n * splits[idx-1])
        end = int(splits[idx] * total_n)
        yield start, end



def partition_coco(coco_instance_data, coco_panoptic_data = None, splits = None):
    images = coco_instance_data['images']
    n_classes = len({category['id'] for category in coco_instance_data['categories']})
    random.shuffle(images)
    partitions = []
    for start, end in partition_indices(len(images), splits):
        partition = {'instance' :  dict(
            categories = coco_instance_data['categories'],
            images = images[start:end],
            annotations = get_annotations(images[start:end], coco_instance_data['annotations'])
        )}
        if coco_panoptic_data is not None:
            partition['panoptic'] = dict(
                categories = coco_panoptic_data['categories'],
                images = images[start:end],
                annotations = get_annotations(images[start:end], coco_panoptic_data['annotations'])
            )
        partitions.append(partition)
    return partitions


def visualize_coco_examples(coco_examples, metadata_catalog, scale = 1.0, max_images = 5, resize_dims = (512,768)):
    images = []
    for idx, example in enumerate(coco_examples):
        if idx > max_images:
            break
        im = cv2.imread(example['file_name'])
        v = Visualizer(im[:, :, ::-1], metadata_catalog, scale=scale)
        out = v.draw_dataset_dict(example)
        images.append(cv2.resize(out.get_image(), resize_dims))
    return Image.fromarray(np.vstack(images))


def visualize_object_inferences(coco_examples, metadata_catalog, predictor, scale = 1.0, max_images = 5, resize_dims = (512, 768)):
    images = []
    for idx, example in enumerate(coco_examples):
        if idx > max_images:
            break
        im = cv2.imread(example['file_name'])
        outputs = predictor(im)
        v = Visualizer(im[:, :, ::-1], metadata_catalog, scale=scale)
        out = v.draw_instance_predictions(outputs["instances"].to("cpu"))
        images.append(cv2.resize(out.get_image()[:, :, ::-1], resize_dims))
    Image.fromarray(np.vstack(images))



def visualize_panoptic_inferences():
    ...

