from pydantic import BaseModel
from typing import Optional
import os
from PIL import Image
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


def get_image(label, image_root, image_id):
    path = os.path.join(image_root, f"{image_id}.jpg")
    if not os.path.exists(path):
        im = Image.fromarray(label.data.data)
        im.save(path)
        w, h = im.size
    else:
        w, h = imagesize.get(path)

    return CocoImage(id=image_id, width=w, height=h, file_name=path.split(os.sep)[-1])
