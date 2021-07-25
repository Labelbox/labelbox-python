from typing import Any, Dict, List, Union

from pydantic.main import BaseModel

from .classification import Checklist, Dropdown, Radio, Text
from .feature import FeatureSchema
from .geometry import Geometry
from .ner import TextEntity


class BaseAnnotation(FeatureSchema):
    """ Base annotation class. Shouldn't be directly instantiated
    """
    extra: Dict[str, Any] = {}


class ClassificationAnnotation(BaseAnnotation):
    """Class representing classification annotations (annotations that don't have a location) """
    value: Union[Text, Checklist, Radio, Dropdown]


class ObjectAnnotation(BaseAnnotation):
    """Class representing objects annotations (non classifications or annotations that have a location)
    """
    value: Union[TextEntity, Geometry]
    classifications: List[ClassificationAnnotation] = []


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
