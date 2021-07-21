from typing import Any, Dict, List, Union

from .classification import Checklist, Dropdown, Radio, Text
from .feature import FeatureSchema
from .geometry import Geometry
from .ner import TextEntity


class BaseAnnotation(FeatureSchema):
    """ Base annotation class. Shouldn't be directly instantiated
    """
    classifications: List["ClassificationAnnotation"] = []
    extra: Dict[str, Any] = {}


class ObjectAnnotation(BaseAnnotation):
    """Class representing objects annotations (non classifications or annotations that have a location)
    """
    value: Union[TextEntity, Geometry]


class ClassificationAnnotation(BaseAnnotation):
    """Class represneting classification annotations (annotations that don't have a location) """
    value: Union[Text, Checklist, Radio, Dropdown]


ClassificationAnnotation.update_forward_refs()


class VideoObjectAnnotation(ObjectAnnotation):
    """
    Class for video objects annotations

    Args:
        frame: The frame index that this annotation corresponds to
        keyframe: Whether or not this annotation was a human generated or interpolated annotation
    """
    frame: int
    keyframe: bool


class VideoClassificationAnnotation(ClassificationAnnotation):
    """
    Class for video classification annotations

    Args:
        frame: The frame index that this annotation corresponds to
    """
    frame: int


VideoObjectAnnotation.update_forward_refs()
ObjectAnnotation.update_forward_refs()
