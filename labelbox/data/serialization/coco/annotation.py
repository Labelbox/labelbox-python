# https://cocodataset.org/#format-data

from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Any, Tuple, Literal, Union, Optional
from pydantic import BaseModel
from ...annotation_types import RasterData, Mask, ObjectAnnotation, Label, Polygon, Point, Rectangle
import numpy as np
import imagesize
from PIL import Image
from tqdm import tqdm
import os
from ...annotation_types.collection import LabelCollection, LabelGenerator


def rle_decoding(rle_arr, w, h):
    indices = []
    for idx, cnt in zip(rle_arr[0::2], rle_arr[1::2]):
        indices.extend(list(range(idx - 1,
                                  idx + cnt - 1)))  # RLE is 1-based index
    mask = np.zeros(h * w, dtype=np.uint8)
    mask[indices] = 1
    return mask.reshape((w, h)).T


def binary_mask_to_rle(binary_mask):
    rle = {'counts': [], 'size': list(binary_mask.shape)}
    counts = rle.get('counts')

    last_elem = 0
    running_length = 0

    for i, elem in enumerate(binary_mask.ravel(order='F')):
        if elem == last_elem:
            pass
        else:
            counts.append(running_length)
            running_length = 0
            last_elem = elem
        running_length += 1

    counts.append(running_length)

    return rle


class CocoImage(BaseModel):
    id: str
    width: int
    height: int
    file_name: str
    license: Optional[int] = None
    flickr_url: Optional[str] = None
    coco_url: Optional[str] = None
    #date_captured: datetime


class RLE(BaseModel):
    counts: List[int]
    size: Tuple[int, int]  # h,w or w,h?


class COCOObjectAnnotation(BaseModel):
    # All segmentations for a particular class in an image...
    # So each image will have one of these for each class present in the image..
    # Annotations only exist if there is data..
    id: str
    image_id: str
    category_id: str
    segmentation: Union[RLE, List[List[float]]]  # [[x1,y1,x2,y2,x3,y3...]]
    area: float
    bbox: Tuple[float, float, float, float]  #[x,y,w,h],
    iscrowd: int = 0  # 0 or 1


class SegmentInfo(BaseModel):
    id: str
    category_id: str
    area: int
    bbox: Tuple[float, float, float, float]  #[x,y,w,h],
    iscrowd: int = 0


class PanopticAnnotation(BaseModel):
    # One to one relationship between image and panoptic annotation
    image_id: str
    file_name: str
    segments_info: List[SegmentInfo]


class Categories(BaseModel):
    id: str
    name: str
    supercategory: str
    isthing: Optional[int]  #Union[Literal[0], Literal[1]] #0 or 1


class PanopticCategories(Categories):
    ...
    #color: Tuple[int,int,int] #[R,G,B],


class CocoInstanceDataset(BaseModel):
    info: Dict[str, Any] = {}
    images: List[CocoImage]
    annotations: List[COCOObjectAnnotation]
    categories: List[Categories]

    @classmethod
    def from_common(cls, labels: LabelCollection, image_root):
        coco_annotations = []
        categories = {}
        images = []
        annot_idx = 0

        for idx, label in tqdm(enumerate(labels)):
            if idx > 200:
                break
            annotations = defaultdict(list)

            for annotation in label.annotations:
                annotations[annotation.name].append(annotation)

            image_id = label.data.uid or idx
            path = os.path.join(image_root, f"{image_id}.jpg")

            if not os.path.exists(path):
                im = Image.fromarray(label.data.data)
                im.save(path)
                w, h = im.size
            else:
                w, h = imagesize.get(path)

            images.append(
                CocoImage(id=image_id, width=w, height=h, file_name=path),)
            for class_name in annotations:
                for annotation in annotations[class_name]:
                    if annotation.name not in categories:
                        categories[annotation.name] = len(categories)

                    if isinstance(annotation.value, Mask):
                        continue  # Not supporting for now..
                        # TODO: Check if coco supports this.. There can only be one mask per class
                        segmentation = RLE(
                            binary_mask_to_rle(
                                annotation.value.raster(binary=True)))
                        shapely = annotation.value.shapely
                        xmin, ymin, xmax, ymax = shapely.bounds
                        coco_annotations.append(
                            id=annot_idx,
                            image_id=image_id,
                            segementation=segmentation,
                            area=shapely.area,
                            bbox=[xmin, ymin, xmax - xmin, ymax - ymin],
                            iscrowd=1)
                        annot_idx += 1
                    elif isinstance(annotation.value, (Polygon, Rectangle)):
                        shapely = annotation.value.shapely
                        xmin, ymin, xmax, ymax = shapely.bounds
                        segmentation = []
                        if isinstance(annotation.value, Polygon):
                            for point in annotation.value.points:
                                segmentation.extend([point.x, point.y])
                        else:
                            box = annotation.value
                            segmentation.extend([
                                box.start.x, box.start.y, box.end.x,
                                box.start.y, box.end.x, box.end.y, box.start.x,
                                box.end.y
                            ])

                        coco_annotations.append(
                            COCOObjectAnnotation(
                                id=annot_idx,
                                image_id=image_id,
                                category_id=categories[annotation.name],
                                segmentation=[segmentation],
                                area=shapely.area,
                                bbox=[xmin, ymin, xmax - xmin, ymax - ymin],
                                iscrowd=0))
                        annot_idx += 1
        return CocoInstanceDataset(info={'image_root': image_root},
                                   images=images,
                                   annotations=coco_annotations,
                                   categories=[
                                       Categories(id=idx,
                                                  name=name,
                                                  supercategory='all',
                                                  isthing=0)
                                       for name, idx in categories.items()
                                   ])

    def to_common(self, image_root):
        category_lookup = {
            category.id: category for category in self.categories
        }
        annotation_lookup = defaultdict(list)
        for annotation in self.annotations:
            annotation_lookup[annotation.image_id].append(annotation)

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
                    # TODO: Check that the order of segmentation is correct..
                    mask = rle_decoding(
                        class_annotations.segmentation.counts,
                        *class_annotations.segmentation.size[::-1])
                    annotations.append(
                        ObjectAnnotation(name=category_lookup[
                            class_annotations.category_id].name,
                                         value=Mask(
                                             mask=RasterData.from_2D_arr(mask),
                                             color=[1, 1, 1])))
                elif isinstance(class_annotations.segmentation, list):
                    for points in class_annotations.segmentation:
                        annotations.append(
                            ObjectAnnotation(
                                name=category_lookup[
                                    class_annotations.category_id].name,
                                value=Polygon(points=[
                                    Point(x=points[i], y=points[i + 1])
                                    for i in range(0, len(points), 2)
                                ])))
                else:
                    breakpoint()
                    raise ValueError("")
            yield Label(data=data, annotations=annotations)


class CocoPanopticDataset(BaseModel):
    info: Dict[str, Any] = {}
    images: List[CocoImage]
    annotations: List[PanopticAnnotation]
    categories: List[PanopticCategories]

    @classmethod
    def from_common(cls, labels: LabelCollection, image_root, seg_root):
        coco_annotations = []
        categories = {}
        images = []
        # TODO: use multiprocessing!!!
        #TODO: Check if directory structure exists and prompt to overwrite..
        # Or set a flag idk.

        for idx, label in tqdm(enumerate(labels)):
            if idx > 200:
                break
            annotations = defaultdict(list)
            for annotation in label.annotations:
                annotations[annotation.name].append(annotation)

            image_id = label.data.uid or idx
            path = os.path.join(image_root, f"{image_id}.jpg")

            if 1:  #not os.path.exists(path):
                im = Image.fromarray(label.data.data)
                im.save(path)
                w, h = im.size
            #else:
            #w,h = imagesize.get(path)

            images.append(
                CocoImage(id=image_id,
                          width=w,
                          height=h,
                          file_name=path.split(os.sep)[-1]),)
            canvas = np.zeros((h, w, 3))
            segments = []

            for class_name in annotations:
                for idx2, annotation in enumerate(annotations[class_name]):
                    if annotation.name not in categories:
                        categories[annotation.name] = len(categories)

                    if isinstance(annotation.value, Mask):
                        mask = annotation.value.raster()
                        shapely = annotation.value.shapely
                        xmin, ymin, xmax, ymax = shapely.bounds
                        canvas = np.where(canvas == (0, 0, 0), mask, canvas)
                        id = (annotation.value.color[0] +
                              annotation.value.color[1] * 256 +
                              annotation.value.color[2] * (256**2))
                        segments.append(
                            SegmentInfo(
                                id=id,
                                category_id=categories[annotation.name],
                                area=shapely.area,
                                bbox=[xmin, ymin, xmax - xmin, ymax - ymin]))
                    elif isinstance(annotation.value, (Polygon, Rectangle)):
                        shapely = annotation.value.shapely
                        xmin, ymin, xmax, ymax = shapely.bounds
                        canvas = annotation.value.raster(
                            height=h,
                            width=w,
                            canvas=canvas,
                            color=(idx2 % 256, idx2 // 256, idx2 // 256 // 256))
                        segments.append(
                            SegmentInfo(
                                id=idx2,
                                category_id=categories[annotation.name],
                                area=shapely.area,
                                bbox=[xmin, ymin, xmax - xmin, ymax - ymin]))

            mask_file = path.replace('.jpg', '.png')
            mask_file = os.path.join(
                seg_root,
                path.split(os.sep)[-1].replace('.jpg', '.png'))
            Image.fromarray(canvas.astype(np.uint8)).save(mask_file)
            coco_annotations.append(
                PanopticAnnotation(image_id=image_id,
                                   file_name=mask_file.split(os.sep)[-1],
                                   segments_info=segments))
        return CocoPanopticDataset(info={
            'image_root': image_root,
            'seg_root': seg_root
        },
                                   images=images,
                                   annotations=coco_annotations,
                                   categories=[
                                       Categories(id=idx,
                                                  name=name,
                                                  supercategory='all',
                                                  isthing=0)
                                       for name, idx in categories.items()
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
                int_id = int(segmentation.id)
                b = int(int_id / 65536)
                remainder = int_id % 65536
                g = int(remainder / 256)
                r = remainder % 256
                #color = [int_id % 256, int_id // 256, int_id // 256 // 256]
                annotations.append(
                    ObjectAnnotation(
                        name=category_lookup[segmentation.category_id].name,
                        value=Mask(mask=mask, color=[r, g, b])))
            data = RasterData(file_path=im_path)
            yield Label(data=data, annotations=annotations)
            del annotation_lookup[image.id]
