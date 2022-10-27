from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, Any, List, Union
from pathlib import Path

from pydantic import BaseModel
from tqdm import tqdm
import numpy as np
from PIL import Image

from ...annotation_types.geometry import Polygon, Rectangle
from ...annotation_types import Label
from ...annotation_types.geometry.mask import Mask
from ...annotation_types.annotation import ObjectAnnotation
from ...annotation_types.data.raster import MaskData, ImageData
from ...annotation_types.collection import LabelCollection
from .categories import Categories, hash_category_name
from .image import CocoImage, get_image, get_image_id, id_to_rgb
from .annotation import PanopticAnnotation, SegmentInfo, get_annotation_lookup


def vector_to_coco_segment_info(canvas: np.ndarray,
                                annotation: ObjectAnnotation,
                                annotation_idx: int, image: CocoImage,
                                category_id: int):

    shapely = annotation.value.shapely
    if shapely.is_empty:
        return

    xmin, ymin, xmax, ymax = shapely.bounds
    canvas = annotation.value.draw(height=image.height,
                                   width=image.width,
                                   canvas=canvas,
                                   color=id_to_rgb(annotation_idx))

    return SegmentInfo(id=annotation_idx,
                       category_id=category_id,
                       area=shapely.area,
                       bbox=[xmin, ymin, xmax - xmin, ymax - ymin]), canvas


def mask_to_coco_segment_info(canvas: np.ndarray, annotation,
                              annotation_idx: int, category_id):
    color = id_to_rgb(annotation_idx)
    mask = annotation.value.draw(color=color)
    shapely = annotation.value.shapely
    if shapely.is_empty:
        return

    xmin, ymin, xmax, ymax = shapely.bounds
    canvas = np.where(canvas == (0, 0, 0), mask, canvas)
    return SegmentInfo(id=annotation_idx,
                       category_id=category_id,
                       area=shapely.area,
                       bbox=[xmin, ymin, xmax - xmin, ymax - ymin]), canvas


def process_label(label: Label,
                  idx: Union[int, str],
                  image_root,
                  mask_root,
                  all_stuff=False):
    """
    Masks become stuff
    Polygon and rectangle become thing
    """
    annotations = get_annotation_lookup(label.annotations)
    image_id = get_image_id(label, idx)
    image = get_image(label, image_root, image_id)
    canvas = np.zeros((image.height, image.width, 3))

    segments = []
    categories = {}
    is_thing = {}

    for class_idx, class_name in enumerate(annotations):
        for annotation_idx, annotation in enumerate(annotations[class_name]):
            categories[annotation.name] = hash_category_name(annotation.name)
            if isinstance(annotation.value, Mask):
                coco_segment_info = mask_to_coco_segment_info(
                    canvas, annotation, class_idx + 1,
                    categories[annotation.name])

                if coco_segment_info is None:
                    # Filter out empty masks
                    continue

                segment, canvas = coco_segment_info
                segments.append(segment)
                is_thing[annotation.name] = 0

            elif isinstance(annotation.value, (Polygon, Rectangle)):
                coco_vector_info = vector_to_coco_segment_info(
                    canvas,
                    annotation,
                    annotation_idx=(class_idx if all_stuff else annotation_idx)
                    + 1,
                    image=image,
                    category_id=categories[annotation.name])

                if coco_segment_info is None:
                    # Filter out empty annotations
                    continue

                segment, canvas = coco_vector_info
                segments.append(segment)
                is_thing[annotation.name] = 1 - int(all_stuff)

    mask_file = str(image.file_name).replace('.jpg', '.png')
    mask_file = Path(mask_root, mask_file)
    Image.fromarray(canvas.astype(np.uint8)).save(mask_file)
    return image, PanopticAnnotation(
        image_id=image_id,
        file_name=Path(mask_file.name),
        segments_info=segments), categories, is_thing


class CocoPanopticDataset(BaseModel):
    info: Dict[str, Any] = {}
    images: List[CocoImage]
    annotations: List[PanopticAnnotation]
    categories: List[Categories]

    @classmethod
    def from_common(cls,
                    labels: LabelCollection,
                    image_root,
                    mask_root,
                    all_stuff,
                    max_workers=8):
        all_coco_annotations = []
        coco_categories = {}
        coco_things = {}
        images = []

        if max_workers:
            with ProcessPoolExecutor(max_workers=max_workers) as exc:
                futures = [
                    exc.submit(process_label, label, idx, image_root, mask_root,
                               all_stuff) for idx, label in enumerate(labels)
                ]
                results = [
                    future.result() for future in tqdm(as_completed(futures))
                ]
        else:
            results = [
                process_label(label, idx, image_root, mask_root, all_stuff)
                for idx, label in enumerate(labels)
            ]

        for result in results:
            images.append(result[0])
            all_coco_annotations.append(result[1])
            coco_categories.update(result[2])
            coco_things.update(result[3])

        category_mapping = {
            category_id: idx + 1
            for idx, category_id in enumerate(coco_categories.values())
        }
        categories = [
            Categories(id=category_mapping[idx],
                       name=name,
                       supercategory='all',
                       isthing=coco_things.get(name, 1))
            for name, idx in coco_categories.items()
        ]

        for annot in all_coco_annotations:
            for segment in annot.segments_info:
                segment.category_id = category_mapping[segment.category_id]

        return CocoPanopticDataset(info={
            'image_root': image_root,
            'mask_root': mask_root
        },
                                   images=images,
                                   annotations=all_coco_annotations,
                                   categories=categories)

    def to_common(self, image_root: Path, mask_root: Path):
        category_lookup = {
            category.id: category for category in self.categories
        }
        annotation_lookup = {
            annotation.image_id: annotation for annotation in self.annotations
        }
        for image in self.images:
            annotations = []
            annotation = annotation_lookup[image.id]

            im_path = Path(image_root, image.file_name)
            if not im_path.exists():
                raise ValueError(
                    f"Cannot find file {im_path}. Make sure `image_root` is set properly"
                )
            if not str(annotation.file_name).endswith('.png'):
                raise ValueError(
                    f"COCO masks must be stored as png files and their extension must be `.png`. Found {annotation.file_name}"
                )
            mask = MaskData(
                file_path=str(Path(mask_root, annotation.file_name)))

            for segmentation in annotation.segments_info:
                category = category_lookup[segmentation.category_id]
                annotations.append(
                    ObjectAnnotation(name=category.name,
                                     value=Mask(mask=mask,
                                                color=id_to_rgb(
                                                    segmentation.id))))
            data = ImageData(file_path=str(im_path))
            yield Label(data=data, annotations=annotations)
            del annotation_lookup[image.id]
