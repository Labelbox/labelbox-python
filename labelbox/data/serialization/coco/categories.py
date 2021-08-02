from pydantic import BaseModel
from typing import Optional


class Categories(BaseModel):
    id: int
    name: str
    supercategory: str
    isthing: Optional[int]
