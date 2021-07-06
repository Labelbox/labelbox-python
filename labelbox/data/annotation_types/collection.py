from typing import Dict, List, Any
from pydantic import BaseModel

from labelbox.data.annotation_types.label import Label


class AnnotationCollection(BaseModel):
    data: List[Label]
