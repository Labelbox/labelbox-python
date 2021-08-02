from collections import defaultdict
from labelbox.data.annotation_types.geometry import Polygon, Rectangle
from labelbox.data.annotation_types import label
from labelbox.data.annotation_types.geometry.mask import Mask
from labelbox.data.annotation_types.annotation import ObjectAnnotation
from labelbox.data.annotation_types.data.raster import RasterData
from labelbox.data.serialization.coco.categories import Categories
from labelbox.data.annotation_types.collection import LabelCollection
from labelbox.data.serialization.coco.image import CocoImage
from labelbox.data.serialization.coco.annotation import PanopticAnnotation, SegmentInfo, get_annotation_lookup
from concurrent.futures import ProcessPoolExecutor, as_completed
from pydantic import BaseModel
import hashlib
from tqdm import tqdm
import os
import numpy as np
from PIL import Image
from typing import Dict, Any, List




def get_image(label, image_root, image_id):
    path = os.path.join(image_root, f"{image_id}.jpg")

    if 1: #not os.path.exists(path):
        im = Image.fromarray(label.data.data)
        im.save(path)
        w, h = im.size
    #else:
    #    w, h = imagesize.get(path)

    return CocoImage(id=image_id, width=w, height=h, file_name=path)



def process_label(label, idx, image_root, seg_root):
    annotations = get_annotation_lookup(label.annotations)
    image_id = idx  #label.data.uid or idx
    path = os.path.join(image_root, f"{image_id}.jpg")

    if 1:  #not os.path.exists(path):
        im = Image.fromarray(label.data.data)
        im.save(path)
        w, h = im.size
    #else:
    #w,h = imagesize.get(path)
    image = CocoImage(id=image_id,
                        width=w,
                        height=h,
                        file_name=path.split(os.sep)[-1])

    canvas = np.zeros((h, w, 3))
    segments = []
    categories = {}
    for class_name in annotations:
        for idx2, annotation in enumerate(annotations[class_name]):
                categories[annotation.name] = int(
                    hashlib.sha256(annotation.name.encode('utf-8')).hexdigest(),
                    16) % 10**8
            if isinstance(annotation.value, Mask):
                segment, canvas = (mask_to_segment_info(
                    canvas, annotation, categories[annotation.name]))
                segments.append(segment)
            elif isinstance(annotation.value, (Polygon, Rectangle)):
                segments.append(
                    vector_to_segment_info(
                        canvas,
                        annotation,
                        annotation_idx=idx2,
                        image=image,
                        category_id=categories[annotation.name]))
        # TODO: Report on unconverted annotations.

    mask_file = path.replace('.jpg', '.png')
    mask_file = os.path.join(
        seg_root,
        path.split(os.sep)[-1].replace('.jpg', '.png'))
    Image.fromarray(canvas.astype(np.uint8)).save(mask_file)

    return PanopticAnnotation(image_id=image_id,
                            file_name=mask_file.split(os.sep)[-1],
                            segments_info=segments), image, categories

class CocoPanopticDataset(BaseModel):
    info: Dict[str, Any] = {}
    images: List[CocoImage]
    annotations: List[PanopticAnnotation]
    categories: List[Categories]

    @classmethod
    def from_common(cls, labels: LabelCollection, image_root, seg_root):
        all_coco_annotations = []
        coco_categories = {}
        images = []
        # TODO: use multiprocessing
        #TODO: Check if directory structure exists and prompt to overwrite..
        # Or set a flag idk.

        with ProcessPoolExecutor(max_workers=12) as exc:
            futures = [
                exc.submit(process_label, label, idx, image_root)
                for idx, label in enumerate(labels)
            ]
            for future in tqdm(as_completed(futures)):
                image, annotation, categories = future.result()
                images.append(image)
                all_coco_annotations.append(annotation)
                coco_categories.update(categories)


        return CocoPanopticDataset(info={
            'image_root': image_root,
            'seg_root': seg_root
        },
                                   images=images,
                                   annotations=all_coco_annotations,
                                   categories=[
                                       Categories(id=idx,
                                                  name=name,
                                                  supercategory='all',
                                                  isthing=0)
                                       for name, idx in coco_categories.items()
                                   ])
    def to_common(self, image_root, seg_root):
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
            # TODO: Make sure it endswith .jpg
            mask = RasterData(file_path=os.path.join(
                seg_root, annotation.file_name.replace('.jpg', '.png')))

            for segmentation in annotation.segments_info:
                color = [
                    segmentation.id % 256, segmentation.id // 256,
                    segmentation.id // 256 // 256
                ]
                annotations.append(
                    ObjectAnnotation(
                        name=category_lookup[segmentation.category_id].name,
                        value=Mask(mask=mask, color=color)))
            data = RasterData(file_path=im_path)
            yield label(data=data, annotations=annotations)
            del annotation_lookup[image.id]


def vector_to_segment_info(canvas: np.ndarray, annotation: ObjectAnnotation,
                           annotation_idx: int, image: CocoImage,
                           category_id: int):
    shapely = annotation.value.shapely
    xmin, ymin, xmax, ymax = shapely.bounds
    canvas = annotation.value.raster(height=image.height,
                                     width=image.width,
                                     canvas=canvas,
                                     color=(annotation_idx % 256,
                                            annotation_idx // 256,
                                            annotation_idx // 256 // 256))

    return SegmentInfo(id=annotation_idx,
                       category_id=category_id,
                       area=shapely.area,
                       bbox=[xmin, ymin, xmax - xmin, ymax - ymin])


def mask_to_segment_info(canvas, annotation, category_id):
    mask = annotation.value.raster()
    shapely = annotation.value.shapely
    xmin, ymin, xmax, ymax = shapely.bounds
    canvas = np.where(canvas == (0, 0, 0), mask, canvas)
    id = (annotation.value.color[0] + annotation.value.color[1] * 256 +
          annotation.value.color[2] * (256**2))
    return SegmentInfo(id=id,
                       category_id=category_id,
                       area=shapely.area,
                       bbox=[xmin, ymin, xmax - xmin, ymax - ymin]), canvas
