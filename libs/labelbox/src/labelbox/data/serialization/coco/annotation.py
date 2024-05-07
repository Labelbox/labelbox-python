from typing import Any, Tuple, List, Union
from pathlib import Path
from collections import defaultdict
import warnings

from ...annotation_types.relationship import RelationshipAnnotation
from ...annotation_types.metrics.confusion_matrix import ConfusionMatrixMetric
from ...annotation_types.metrics.scalar import ScalarMetric
from ...annotation_types.video import VideoMaskAnnotation
from ...annotation_types.annotation import ObjectAnnotation
from ...annotation_types.classification.classification import ClassificationAnnotation

from .... import pydantic_compat
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
    """Get annotations from Label.annotations objects

    Args:
        annotations (Label.annotations): Annotations attached to labelbox Label object used as private method
    """
    annotation_lookup = defaultdict(list)
    for annotation in annotations:
        # Provide a default value of None if the attribute doesn't exist
        attribute_value = getattr(annotation, 'image_id', None) or getattr(annotation, 'name', None)
        annotation_lookup[attribute_value].append(annotation)
    return annotation_lookup 


class SegmentInfo(pydantic_compat.BaseModel):
    id: int
    category_id: int
    area: int
    bbox: Tuple[float, float, float, float]  #[x,y,w,h],
    iscrowd: int = 0


class RLE(pydantic_compat.BaseModel):
    counts: List[int]
    size: Tuple[int, int]  # h,w or w,h?


class COCOObjectAnnotation(pydantic_compat.BaseModel):
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
