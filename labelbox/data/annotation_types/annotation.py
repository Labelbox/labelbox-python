from typing import List, Optional, Union, Dict, Any
from uuid import uuid4
from pydantic import BaseModel, root_validator
from pydantic.error_wrappers import ValidationError

from labelbox.data.annotation_types.reference import FeatureSchemaRef
from labelbox.data.annotation_types.classification import Classification, Subclass
from labelbox.data.annotation_types.ner import TextEntity
from labelbox.data.annotation_types.geometry import Geometry


class Annotation(FeatureSchemaRef):
    classifications: List[Subclass] = []
    value: Union[Classification, Geometry, TextEntity]
    extra: Dict[str, Any] = {}


class Frames(BaseModel):
    start: int
    end: int

    @root_validator
    def validate_start_end(cls, values):
        if (isinstance(values['start'], int) and
                values['start'] >= values['end']):
            raise ValidationError(
                "End frame index must be greater or equal to start")
        if values['start'] < 0:
            raise ValidationError("frame index cannot be negative")
        return values


class VideoAnnotation(Annotation):
    frames: List[Frames]
