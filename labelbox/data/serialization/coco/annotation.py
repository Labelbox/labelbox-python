
# https://cocodataset.org/#format-data

from datetime import datetime
from typing import List


class CocoImage:
    id: int
    width: int
    height: int
    file_name: str
    license: int
    flickr_url: str
    coco_url: str
    date_captured: datetime

class CocoPanopticDataset:
    ...

class CocoInstanceDataset:
    images: List[CocoImage]
    annotations: List[ObjectAnnotation]

class ObjectAnnotation:
    id: str
    image_id: str
    category_id: str
    segmentation: polygon
    area: float
    bbox: [x,y,w,h],
    iscrowd: 0


class SegmentInfo:
    id: int
    category_id: int
    area: int
    bbox: [x,y,w, h],
    iscrowd: 0


class Categories:
    "id": int,
    "name": str,
    "supercategory": str,
    "isthing": 0 or 1,
    "color": [R,G,B],




