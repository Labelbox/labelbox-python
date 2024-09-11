from pathlib import Path

from typing import Optional, Tuple
from PIL import Image
import imagesize

from .path import PathSerializerMixin
from ...annotation_types import Label


class CocoImage(PathSerializerMixin):
    id: int
    width: int
    height: int
    file_name: Path
    license: Optional[int] = None
    flickr_url: Optional[str] = None
    coco_url: Optional[str] = None


def get_image_id(label: Label, idx: int) -> int:
    if label.data.file_path is not None:
        file_name = label.data.file_path.replace(".jpg", "")
        if file_name.isdecimal():
            return file_name
    return idx


def get_image(label: Label, image_root: Path, image_id: str) -> CocoImage:
    path = Path(image_root, f"{image_id}.jpg")
    if not path.exists():
        im = Image.fromarray(label.data.value)
        im.save(path)
        w, h = im.size
    else:
        w, h = imagesize.get(str(path))
    return CocoImage(id=image_id, width=w, height=h, file_name=Path(path.name))


def id_to_rgb(id: int) -> Tuple[int, int, int]:
    digits = []
    for _ in range(3):
        digits.append(id % 256)
        id //= 256
    return digits


def rgb_to_id(red: int, green: int, blue: int) -> int:
    id = blue * 256 * 256
    id += green * 256
    id += red
    return id
