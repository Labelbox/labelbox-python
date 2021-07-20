from typing import Any, Dict, List, Union

from labelbox.data.annotation_types.classification.classification import (
    CheckList, Dropdown, Radio, Text)
from labelbox.data.annotation_types.geometry import Geometry
from labelbox.data.annotation_types.ner import TextEntity
from labelbox.data.annotation_types.reference import FeatureSchemaRef


class BaseAnnotation(FeatureSchemaRef):
    classifications: List["ClassificationAnnotation"] = []
    extra: Dict[str, Any] = {}


class ObjectAnnotation(BaseAnnotation):
    value: Union[TextEntity, Geometry]


class ClassificationAnnotation(BaseAnnotation):
    value: Union[Text, CheckList, Radio, Dropdown]


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
