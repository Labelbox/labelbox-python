from typing import Tuple, List, Union
from pathlib import Path
from collections import defaultdict

from pydantic import BaseModel
import numpy as np

from .path import PathSerializerMixin


def rle_decoding(rle_arr: List[int], w: int, h: int) -> np.ndarray:
    indices = []
    for idx, cnt in zip(rle_arr[0::2], rle_arr[1::2]):
        indices.extend(list(range(idx - 1,
                                  idx + cnt - 1)))  # RLE is 1-based index
    mask = np.zeros(h * w, dtype=np.uint8)
    mask[indices] = 1
    return mask.reshape((w, h)).T


def get_annotation_lookup(annotations):
    annotation_lookup = defaultdict(list)
    for annotation in annotations:
        annotation_lookup[getattr(annotation, 'image_id', None) or
                          getattr(annotation, 'name')].append(annotation)
    return annotation_lookup


class SegmentInfo(BaseModel):
    id: int
    category_id: int
    area: int
    bbox: Tuple[float, float, float, float]  #[x,y,w,h],
    iscrowd: int = 0


class RLE(BaseModel):
    counts: List[int]
    size: Tuple[int, int]  # h,w or w,h?


class COCOObjectAnnotation(BaseModel):
    # All segmentations for a particular class in an image...
    # So each image will have one of these for each class present in the image..
    # Annotations only exist if there is data..
    id: int
    image_id: int
    category_id: int
    segmentation: Union[RLE, List[List[float]]]  # [[x1,y1,x2,y2,x3,y3...]]
    area: float
    bbox: Tuple[float, float, float, float]  #[x,y,w,h],
    iscrowd: int = 0


class PanopticAnnotation(PathSerializerMixin):
    # One to one relationship between image and panoptic annotation
    image_id: int
    file_name: Path
    segments_info: List[SegmentInfo]
