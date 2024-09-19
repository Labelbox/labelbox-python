from typing import Optional

from pydantic import model_serializer

from ..base_annotation import BaseAnnotation
from ..mixins import ConfidenceMixin, CustomMetricsMixin
from .checklist import Checklist


class ClassificationAnnotation(
    BaseAnnotation, ConfidenceMixin, CustomMetricsMixin
):
    """Classification annotations (non localized)

    >>> ClassificationAnnotation(
    >>>     value=Text(answer="my caption message"),
    >>>     feature_schema_id="my-feature-schema-id"
    >>> )

    Args:
        name (Optional[str])
        classifications (Optional[List[ClassificationAnnotation]]): Optional sub classification of the annotation
        feature_schema_id (Optional[Cuid])
        value (Union[Text, Checklist, Radio])
        extra (Dict[str, Any])
    """

    value: Checklist
    message_id: Optional[str] = None

    @model_serializer(mode='wrap')
    def serialize_label(self, handler, info):
        res = handler(self)
        value = res.pop("value")
        res["answer"] = value["answer"]
        return res
