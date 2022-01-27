# https://cocodataset.org/#format-data

from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any, Dict, List, Tuple
from pathlib import Path

import numpy as np
from tqdm import tqdm
from pydantic import BaseModel

from ...annotation_types import ImageData, MaskData, Mask, ObjectAnnotation, Label, Polygon, Point, Rectangle
from ...annotation_types.collection import LabelCollection
from .categories import Categories, hash_category_name
from .annotation import COCOObjectAnnotation, RLE, get_annotation_lookup, rle_decoding
from .image import CocoImage, get_image, get_image_id


def mask_to_coco_object_annotation(annotation: ObjectAnnotation, annot_idx: int,
                                   image_id: int,
                                   category_id: int) -> COCOObjectAnnotation:
    # This is going to fill any holes into the multipolygon
    # If you need to support holes use the panoptic data format
    shapely = annotation.value.shapely.simplify(1).buffer(0)
    if shapely.is_empty:
        shapely = annotation.value.shapely.simplify(1).buffer(0.01)
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


def vector_to_coco_object_annotation(annotation: ObjectAnnotation,
                                     annot_idx: int, image_id: int,
                                     category_id: int) -> COCOObjectAnnotation:
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


def rle_to_common(class_annotations: COCOObjectAnnotation,
                  class_name: str) -> ObjectAnnotation:
    mask = rle_decoding(class_annotations.segmentation.counts,
                        *class_annotations.segmentation.size[::-1])
    return ObjectAnnotation(name=class_name,
                            value=Mask(mask=MaskData.from_2D_arr(mask),
                                       color=[1, 1, 1]))


def segmentations_to_common(class_annotations: COCOObjectAnnotation,
                            class_name: str) -> List[ObjectAnnotation]:
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


def process_label(
    label: Label,
    idx: int,
    image_root: str,
    max_annotations_per_image=10000
) -> Tuple[np.ndarray, List[COCOObjectAnnotation], Dict[str, str]]:
    annot_idx = idx * max_annotations_per_image
    image_id = get_image_id(label, idx)
    image = get_image(label, image_root, image_id)
    coco_annotations = []
    annotation_lookup = get_annotation_lookup(label.annotations)
    categories = {}
    for class_name in annotation_lookup:
        for annotation in annotation_lookup[class_name]:
            if annotation.name not in categories:
                categories[annotation.name] = hash_category_name(
                    annotation.name)
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
    def from_common(cls,
                    labels: LabelCollection,
                    image_root: Path,
                    max_workers=8):
        all_coco_annotations = []
        categories = {}
        images = []
        futures = []
        coco_categories = {}

        if max_workers:
            with ProcessPoolExecutor(max_workers=max_workers) as exc:
                futures = [
                    exc.submit(process_label, label, idx, image_root)
                    for idx, label in enumerate(labels)
                ]
                results = [
                    future.result() for future in tqdm(as_completed(futures))
                ]
        else:
            results = [
                process_label(label, idx, image_root)
                for idx, label in enumerate(labels)
            ]

        for result in results:
            images.append(result[0])
            all_coco_annotations.extend(result[1])
            coco_categories.update(result[2])

        category_mapping = {
            category_id: idx + 1
            for idx, category_id in enumerate(coco_categories.values())
        }
        categories = [
            Categories(id=category_mapping[idx],
                       name=name,
                       supercategory='all',
                       isthing=1) for name, idx in coco_categories.items()
        ]
        for annot in all_coco_annotations:
            annot.category_id = category_mapping[annot.category_id]

        return CocoInstanceDataset(info={'image_root': image_root},
                                   images=images,
                                   annotations=all_coco_annotations,
                                   categories=categories)

    def to_common(self, image_root):
        category_lookup = {
            category.id: category for category in self.categories
        }
        annotation_lookup = get_annotation_lookup(self.annotations)

        for image in self.images:
            im_path = Path(image_root, image.file_name)
            if not im_path.exists():
                raise ValueError(
                    f"Cannot find file {im_path}. Make sure `image_root` is set properly"
                )

            data = ImageData(file_path=str(im_path))
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
