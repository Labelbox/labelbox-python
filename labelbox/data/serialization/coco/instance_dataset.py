# https://cocodataset.org/#format-data

from labelbox.data.serialization.coco.categories import Categories
from labelbox.data.serialization.coco.annotation import COCOObjectAnnotation, RLE, get_annotation_lookup, rle_decoding
from labelbox.data.serialization.coco.image import CocoImage
from typing import Any, Dict, List
from pydantic import BaseModel
from ...annotation_types import RasterData, Mask, ObjectAnnotation, Label, Polygon, Point, Rectangle
import numpy as np
import imagesize
from PIL import Image
import hashlib
from tqdm import tqdm
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from ...annotation_types.collection import LabelCollection


def get_image(label, image_root, image_id):
    path = os.path.join(image_root, f"{image_id}.jpg")

    if not os.path.exists(path):
        im = Image.fromarray(label.data.data)
        im.save(path)
        w, h = im.size
    else:
        w, h = imagesize.get(path)

    return CocoImage(id=image_id, width=w, height=h, file_name=path)


def mask_to_coco_object_annotation(annotation: ObjectAnnotation, annot_idx,
                                   image_id, category_id):
    # This is going to fill any holes into the multipolygon
    # If you need to support holes use the panoptic data format
    shapely = annotation.value.shapely.simplify(1).buffer(0)
    xmin, ymin, xmax, ymax = shapely.bounds
    # Iterate over polygon once or multiple polygon for each item
    area = shapely.area
    if shapely.type == 'Polygon':
        shapely = [shapely]

    return COCOObjectAnnotation(
        id=annot_idx,
        image_id=image_id,
        category_id=category_id,
        segmentation=[
            np.array(s.exterior.coords).ravel().tolist() for s in shapely
        ],
        area=area,
        bbox=[xmin, ymin, xmax - xmin, ymax - ymin],
        iscrowd=0)


def vector_to_coco_object_annotation(annotation: ObjectAnnotation, annot_idx,
                                     image_id, category_id):
    shapely = annotation.value.shapely
    xmin, ymin, xmax, ymax = shapely.bounds
    segmentation = []
    if isinstance(annotation.value, Polygon):
        for point in annotation.value.points:
            segmentation.extend([point.x, point.y])
    else:
        box = annotation.value
        segmentation.extend([
            box.start.x, box.start.y, box.end.x, box.start.y, box.end.x,
            box.end.y, box.start.x, box.end.y
        ])

    return COCOObjectAnnotation(id=annot_idx,
                                image_id=image_id,
                                category_id=category_id,
                                segmentation=[segmentation],
                                area=shapely.area,
                                bbox=[xmin, ymin, xmax - xmin, ymax - ymin],
                                iscrowd=0)


def rle_to_common(class_annotations, class_name):
    mask = rle_decoding(class_annotations.segmentation.counts,
                        *class_annotations.segmentation.size[::-1])
    return ObjectAnnotation(name=class_name,
                            value=Mask(mask=RasterData.from_2D_arr(mask),
                                       color=[1, 1, 1]))


def segmentations_to_common(class_annotations, class_name):
    # Technically it is polygons. But the key in coco is called segmentations..
    annotations = []
    for points in class_annotations.segmentation:
        annotations.append(
            ObjectAnnotation(name=class_name,
                             value=Polygon(points=[
                                 Point(x=points[i], y=points[i + 1])
                                 for i in range(0, len(points), 2)
                             ])))
    return annotations


def process_label(label, idx, image_root):
    annot_idx = idx * 10000
    image_id = idx  # everything has to be an int.. #label.data.uid or idx
    image = get_image(label, image_root, idx)
    coco_annotations = []
    annotation_lookup = get_annotation_lookup(label.annotations)
    categories = {}
    for class_name in annotation_lookup:
        for annotation in annotation_lookup[class_name]:
            if annotation.name not in categories:
                categories[annotation.name] = int(
                    hashlib.sha256(annotation.name.encode('utf-8')).hexdigest(),
                    16) % 10**8
            if isinstance(annotation.value, Mask):
                coco_annotations.append(
                    mask_to_coco_object_annotation(annotation, annot_idx,
                                                   image_id,
                                                   categories[annotation.name]))
            elif isinstance(annotation.value, (Polygon, Rectangle)):
                coco_annotations.append(
                    vector_to_coco_object_annotation(
                        annotation, annot_idx, image_id,
                        categories[annotation.name]))
            annot_idx += 1
    return image, coco_annotations, categories


class CocoInstanceDataset(BaseModel):
    info: Dict[str, Any] = {}
    images: List[CocoImage]
    annotations: List[COCOObjectAnnotation]
    categories: List[Categories]

    @classmethod
    def from_common(cls, labels: LabelCollection, image_root):
        all_coco_annotations = []
        categories = {}
        images = []
        futures = []
        coco_categories = {}

        with ProcessPoolExecutor(max_workers=12) as exc:
            futures = [
                exc.submit(process_label, label, idx, image_root)
                for idx, label in enumerate(labels)
            ]
            for future in tqdm(as_completed(futures)):
                image, annotations, categories = future.result()
                images.append(image)
                all_coco_annotations.extend(annotations)
                coco_categories.update(categories)

        return CocoInstanceDataset(info={'image_root': image_root},
                                   images=images,
                                   annotations=all_coco_annotations,
                                   categories=[
                                       Categories(id=idx,
                                                  name=name,
                                                  supercategory='all',
                                                  isthing=0)
                                       for name, idx in coco_categories.items()
                                   ])

    def to_common(self, image_root):
        category_lookup = {
            category.id: category for category in self.categories
        }
        annotation_lookup = get_annotation_lookup(self.annotations)

        for image in self.images:
            im_path = os.path.join(image_root, image.file_name)
            if not os.path.exists(im_path):
                raise ValueError(
                    f"Cannot find file {im_path}. Make sure `image_root` is set properly"
                )

            data = RasterData(file_path=im_path)
            annotations = []
            for class_annotations in annotation_lookup[image.id]:
                if isinstance(class_annotations.segmentation, RLE):
                    annotations.append(
                        rle_to_common(
                            class_annotations, category_lookup[
                                class_annotations.category_id].name))
                elif isinstance(class_annotations.segmentation, list):
                    annotations.extend(
                        segmentations_to_common(
                            class_annotations, category_lookup[
                                class_annotations.category_id].name))
            yield Label(data=data, annotations=annotations)
