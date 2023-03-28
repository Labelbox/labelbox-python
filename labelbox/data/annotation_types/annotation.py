import abc
from typing import Any, Dict, List, Optional, Union
from pydantic import PrivateAttr, validator
from uuid import UUID, uuid4

from labelbox.data.mixins import ConfidenceMixin

from .classification import Checklist, Dropdown, Radio, Text
from .feature import FeatureSchema
from .geometry import Geometry, Rectangle, Point
from .ner import DocumentEntity, TextEntity, ConversationEntity


class BaseAnnotation(FeatureSchema, abc.ABC):
    """ Base annotation class. Shouldn't be directly instantiated
    """
    _uuid: UUID = PrivateAttr()
    extra: Dict[str, Any] = {}

    def __init__(self, **data):
        super().__init__(**data)
        extra_uuid = data.get("extra", {}).get("uuid")
        self._uuid = data.get("_uuid") or extra_uuid or uuid4()


class ClassificationAnnotation(BaseAnnotation, ConfidenceMixin):
    """Classification annotations (non localized)

    >>> ClassificationAnnotation(
    >>>     value=Text(answer="my caption message"),
    >>>     feature_schema_id="my-feature-schema-id"
    >>> )

    Args:
        name (Optional[str])
        feature_schema_id (Optional[Cuid])
        value (Union[Text, Checklist, Radio, Dropdown])
        message_id (Optional[str]) Message id for conversational text
        extra (Dict[str, Any])
     """

    value: Union[Text, Checklist, Radio, Dropdown]
    message_id: Optional[str] = None


class ObjectAnnotation(BaseAnnotation, ConfidenceMixin):
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
    value: Union[TextEntity, ConversationEntity, DocumentEntity, Geometry]
    classifications: List[ClassificationAnnotation] = []
