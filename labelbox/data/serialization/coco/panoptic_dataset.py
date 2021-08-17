from labelbox.data.annotation_types.geometry import Polygon, Rectangle
from labelbox.data.annotation_types import Label
from labelbox.data.annotation_types.geometry.mask import Mask
from labelbox.data.annotation_types.annotation import ObjectAnnotation
from labelbox.data.annotation_types.data.raster import MaskData, ImageData
from labelbox.data.serialization.coco.categories import Categories, hash_category_name
from labelbox.data.annotation_types.collection import LabelCollection
from labelbox.data.serialization.coco.image import CocoImage, get_image, get_image_id, id_to_rgb, rgb_to_id
from labelbox.data.serialization.coco.annotation import PanopticAnnotation, SegmentInfo, get_annotation_lookup
from concurrent.futures import ProcessPoolExecutor, as_completed
from pydantic import BaseModel
from tqdm import tqdm
import os
import numpy as np
from PIL import Image
from typing import Dict, Any, List, Union


def vector_to_coco_segment_info(canvas: np.ndarray,
                                annotation: ObjectAnnotation,
                                annotation_idx: int, image: CocoImage,
                                category_id: int):
    shapely = annotation.value.shapely
    xmin, ymin, xmax, ymax = shapely.bounds
    canvas = annotation.value.draw(height=image.height,
                                   width=image.width,
                                   canvas=canvas,
                                   color=id_to_rgb(annotation_idx))

    return SegmentInfo(id=annotation_idx,
                       category_id=category_id,
                       area=shapely.area,
                       bbox=[xmin, ymin, xmax - xmin, ymax - ymin])


def mask_to_coco_segment_info(canvas: np.ndarray, annotation, category_id):
    # Expects a unique color for each class....
    # Also there is a possible conflict with vector classes being draw. TODO: Use ID instead
    mask = annotation.value.draw()
    shapely = annotation.value.shapely
    xmin, ymin, xmax, ymax = shapely.bounds
    canvas = np.where(canvas == (0, 0, 0), mask, canvas)
    id = rgb_to_id(*annotation.value.color)
    return SegmentInfo(id=id,
                       category_id=category_id,
                       area=shapely.area,
                       bbox=[xmin, ymin, xmax - xmin, ymax - ymin]), canvas


def process_label(label: Label, idx: Union[int, str], image_root, mask_root, all_stuff = False):
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
                segment, canvas = (mask_to_coco_segment_info(
                    canvas, annotation, categories[annotation.name]))
                segments.append(segment)
                is_thing[annotation.name] = 0

            elif isinstance(annotation.value, (Polygon, Rectangle)):
                segments.append(
                    vector_to_coco_segment_info(
                        canvas,
                        annotation,
                        annotation_idx=(class_idx if all_stuff else annotation_idx) + 1,
                        image=image,
                        category_id=categories[annotation.name]))
                is_thing[annotation.name] = 1 - int(all_stuff)
        # TODO: Report on unconverted annotations.

    mask_file = image.file_name.replace('.jpg', '.png')
    mask_file = os.path.join(mask_root, mask_file)
    Image.fromarray(canvas.astype(np.uint8)).save(mask_file)
    return image, PanopticAnnotation(
        image_id=image_id,
        file_name=mask_file.split(os.sep)[-1],
        segments_info=segments), categories, is_thing


class CocoPanopticDataset(BaseModel):
    info: Dict[str, Any] = {}
    images: List[CocoImage]
    annotations: List[PanopticAnnotation]
    categories: List[Categories]

    @classmethod
    def from_common(cls, labels: LabelCollection, image_root, mask_root, all_stuff):
        all_coco_annotations = []
        coco_categories = {}
        coco_things = {}
        images = []
        with ProcessPoolExecutor(max_workers=8) as exc:
            futures = [
                exc.submit(process_label, label, idx, image_root, mask_root, all_stuff)
                for idx, label in enumerate(labels)
            ]
            for future in tqdm(as_completed(futures)):
                image, annotation, categories, things = future.result()
                images.append(image)
                all_coco_annotations.append(annotation)
                coco_categories.update(categories)
                coco_things.update(things)

        return CocoPanopticDataset(info={
            'image_root': image_root,
            'mask_root': mask_root
        },
                                   images=images,
                                   annotations=all_coco_annotations,
                                   categories=[
                                       Categories(id=idx,
                                                  name=name,
                                                  supercategory='all',
                                                  isthing=coco_things.get(
                                                      name, 1))
                                       for name, idx in coco_categories.items()
                                   ])

    def to_common(self, image_root, mask_root):
        category_lookup = {
            category.id: category for category in self.categories
        }
        annotation_lookup = {
            annotation.image_id: annotation for annotation in self.annotations
        }
        for image in self.images:
            annotations = []
            annotation = annotation_lookup[image.id]
            im_path = os.path.join(image_root, image.file_name)
            if not os.path.exists(im_path):
                raise ValueError(
                    f"Cannot find file {im_path}. Make sure `image_root` is set properly"
                )

            if not annotation.file_name.endswith('.png'):
                raise ValueError(
                    f"COCO masks must be stored as png files and their extension must be `.png`. Found {annotation.file_name}"
                )
            mask = MaskData(
                file_path=os.path.join(mask_root, annotation.file_name))

            for segmentation in annotation.segments_info:
                category = category_lookup[segmentation.category_id]
                annotations.append(
                    ObjectAnnotation(name=category.name,
                                     value=Mask(mask=mask,
                                                color=id_to_rgb(
                                                    segmentation.id))))
            data = ImageData(file_path=im_path)
            yield Label(data=data, annotations=annotations)
            del annotation_lookup[image.id]
