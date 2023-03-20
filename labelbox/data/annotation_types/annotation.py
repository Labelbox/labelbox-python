import abc
from typing import Any, Dict, List, Optional, Union

from enum import Enum
from typing import List, Optional, Union
from labelbox.data.annotation_types.base_annotation import BaseAnnotation

from labelbox.data.mixins import ConfidenceMixin

from labelbox.data.annotation_types.classification.classification import Checklist, ClassificationAnnotation, Radio, Text, Dropdown
from .geometry import Geometry
from .ner import DocumentEntity, TextEntity, ConversationEntity


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
