from labelbox.data.annotation_types import Label
from pydantic import BaseModel
from typing import Optional, Tuple
import os
from PIL import Image
import hashlib
import imagesize


class CocoImage(BaseModel):
    id: int
    width: int
    height: int
    file_name: str
    license: Optional[int] = None
    flickr_url: Optional[str] = None
    coco_url: Optional[str] = None
    #date_captured: datetime


def get_image_id(label: Label, idx: int):
    if label.data.file_path is not None:
        file_name = label.data.file_path.replace(".jpg", "")
        if file_name.isdecimal():
            return label.data.file_path.replace(".jpg", "")
    return idx


def get_image(label: Label, image_root, image_id):
    path = os.path.join(image_root, f"{image_id}.jpg")
    if not os.path.exists(path):
        im = Image.fromarray(label.data.value)
        im.save(path)
        w, h = im.size
    else:
        w, h = imagesize.get(path)
    return CocoImage(id=image_id,
                     width=w,
                     height=h,
                     file_name=path.split(os.sep)[-1])


def id_to_rgb(id: int) -> Tuple[int, int, int]:
    blue = id // (256 * 256)
    rem = id - (blue * 256 * 256)
    green = rem // 256
    red = rem - (256 * green)
    return red, green, blue


def rgb_to_id(red: int, green: int, blue: int) -> int:
    id = blue * 256 * 256
    id += (green * 256)
    id += red
    return id
