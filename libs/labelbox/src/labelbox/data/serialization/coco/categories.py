import sys
from hashlib import md5

from .... import pydantic_compat


class Categories(pydantic_compat.BaseModel):
    id: int
    name: str
    supercategory: str
    isthing: int = 1


def hash_category_name(name: str) -> int:
    return int.from_bytes(
        md5(name.encode('utf-8')).hexdigest().encode('utf-8'), 'little')
