import sys

from pydantic import BaseModel


class Categories(BaseModel):
    id: int
    name: str
    supercategory: str
    isthing: int = 1


def hash_category_name(name: str) -> int:
    return hash(name) + sys.maxsize
