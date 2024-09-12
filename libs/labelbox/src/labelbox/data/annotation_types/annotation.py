from typing import List, Union

from labelbox.data.annotation_types.base_annotation import BaseAnnotation
from labelbox.data.annotation_types.geometry.geometry import Geometry

from labelbox.data.mixins import ConfidenceMixin, CustomMetricsMixin

from labelbox.data.annotation_types.classification.classification import (
    ClassificationAnnotation,
)
from .ner import DocumentEntity, TextEntity, ConversationEntity
from typing import Optional


class ObjectAnnotation(BaseAnnotation, ConfidenceMixin, CustomMetricsMixin):
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
    classifications: Optional[List[ClassificationAnnotation]] = []
