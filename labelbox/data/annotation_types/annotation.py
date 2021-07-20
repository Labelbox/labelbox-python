from typing import Any, Dict, List, Union

from .classification import Checklist, Dropdown, Radio, Text
from .feature import FeatureSchemaRef
from .geometry import Geometry
from .ner import TextEntity


class BaseAnnotation(FeatureSchemaRef):
    classifications: List["ClassificationAnnotation"] = []
    extra: Dict[str, Any] = {}


class ObjectAnnotation(BaseAnnotation):
    value: Union[TextEntity, Geometry]


class ClassificationAnnotation(BaseAnnotation):
    value: Union[Text, Checklist, Radio, Dropdown]


ClassificationAnnotation.update_forward_refs()


class VideoObjectAnnotation(ObjectAnnotation):
    frame: int
    keyframe: bool


class VideoClassificationAnnotation(ClassificationAnnotation):
    frame: int


AnnotationType = Union[ClassificationAnnotation, ObjectAnnotation]
VideoAnnotationType = Union[VideoObjectAnnotation,
                            VideoClassificationAnnotation]

VideoObjectAnnotation.update_forward_refs()
ObjectAnnotation.update_forward_refs()
