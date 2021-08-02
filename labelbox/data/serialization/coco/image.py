from pydantic import BaseModel
from typing import Optional


class CocoImage(BaseModel):
    id: int
    width: int
    height: int
    file_name: str
    license: Optional[int] = None
    flickr_url: Optional[str] = None
    coco_url: Optional[str] = None
    #date_captured: datetime
