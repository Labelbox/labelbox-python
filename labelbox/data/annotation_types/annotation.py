import abc
from typing import Any, Dict, List, Optional, Union

from .classification import Checklist, Dropdown, Radio, Text
from .feature import FeatureSchema
from .geometry import Geometry, Rectangle, Point
from .ner import TextEntity


class BaseAnnotation(FeatureSchema, abc.ABC):
    """ Base annotation class. Shouldn't be directly instantiated
    """
    extra: Dict[str, Any] = {}


class ClassificationAnnotation(BaseAnnotation):
    """Classification annotations (non localized)

    >>> ClassificationAnnotation(
    >>>     value=Text(answer="my caption message"),
    >>>     feature_schema_id="my-feature-schema-id"
    >>> )

    Args:
        name (Optional[str])
        feature_schema_id (Optional[Cuid])
        value (Union[Text, Checklist, Radio, Dropdown])
        extra (Dict[str, Any])
     """

    value: Union[Text, Checklist, Radio, Dropdown]


class ObjectAnnotation(BaseAnnotation):
    """Generic localized annotation (non classifications)

    >>> ObjectAnnotation(
    >>>     value=Rectangle(
    >>>        start=Point(x=0, y=0),
    >>>        end=Point(x=1, y=1)
    >>>     ),
    >>>     feature_schema_id="my-feature-schema-id"
    >>> )

    Args:
        name (Optional[str])
        feature_schema_id (Optional[Cuid])
        value (Union[TextEntity, Geometry]): Localization of the annotation
        classifications (Optional[List[ClassificationAnnotation]]): Optional sub classification of the annotation
        extra (Dict[str, Any])
    """
    value: Union[TextEntity, Geometry]
    classifications: List[ClassificationAnnotation] = []


class VideoObjectAnnotation(ObjectAnnotation):
    """Video object annotation

    >>> VideoObjectAnnotation(
    >>>     keyframe=True,
    >>>     frame=10,
    >>>     value=Rectangle(
    >>>        start=Point(x=0, y=0),
    >>>        end=Point(x=1, y=1)
    >>>     ),
    >>>     feature_schema_id="my-feature-schema-id"
    >>>)

    Args:
        name (Optional[str])
        feature_schema_id (Optional[Cuid])
        value (Geometry)
        frame (Int): The frame index that this annotation corresponds to
        keyframe (bool): Whether or not this annotation was a human generated or interpolated annotation
        segment_id (Optional[Int]): Index of video segment this annotation belongs to
        classifications (List[ClassificationAnnotation]) = []
        extra (Dict[str, Any])
    """
    frame: int
    keyframe: bool
    segment_index: Optional[int] = None


class VideoClassificationAnnotation(ClassificationAnnotation):
    """Video classification

    Args:
        name (Optional[str])
        feature_schema_id (Optional[Cuid])
        value (Union[Text, Checklist, Radio, Dropdown])
        frame (int): The frame index that this annotation corresponds to
        segment_id (Optional[Int]): Index of video segment this annotation belongs to
        extra (Dict[str, Any])
    """
    frame: int
    segment_index: Optional[int] = None
