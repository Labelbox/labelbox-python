from typing import List, Optional, Union, Dict, Any
from uuid import uuid4
from pydantic import BaseModel, root_validator, validator
from pydantic.error_wrappers import ValidationError

from labelbox.data.annotation_types.reference import FeatureSchemaRef
from labelbox.data.annotation_types.classification import Classification, Subclass
from labelbox.data.annotation_types.ner import TextEntity
from labelbox.data.annotation_types.geometry import Geometry


class Annotation(FeatureSchemaRef):
    classifications: List[Subclass] = []
    value: Union[Classification, TextEntity, Geometry]
    extra: Dict[str, Any] = {}

class VideoAnnotation(Annotation):
    frame: int
    keyframe: Optional[bool] = None # Can be None if Annotation is None

