from pydantic import BaseModel
from typing import Optional
import hashlib


class Categories(BaseModel):
    id: int
    name: str
    supercategory: str
    isthing: int = 1


def hash_category_name(name: str) -> int:
    return int(hashlib.sha256(name.encode('utf-8')).hexdigest(), 16) % 10000
