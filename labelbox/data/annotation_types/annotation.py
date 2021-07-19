from labelbox.data.annotation_types.classification.classification import Dropdown, Text, CheckList, Radio
from typing import List, Union, Dict, Any

from labelbox.data.annotation_types.reference import FeatureSchemaRef
from labelbox.data.annotation_types.ner import TextEntity
from labelbox.data.annotation_types.geometry import Geometry


class BaseAnnotation(FeatureSchemaRef):
    classifications: List["ClassificationAnnotation"] = []
    extra: Dict[str, Any] = {}


class ObjectAnnotation(BaseAnnotation):
    value: Union[TextEntity, Geometry]


class ClassificationAnnotation(BaseAnnotation):
    value: Union[Dropdown, Text, CheckList, Radio]


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
