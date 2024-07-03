from typing import Union

from labelbox.data.annotation_types.base_annotation import BaseAnnotation

from labelbox.data.mixins import ConfidenceMixin, CustomMetricsMixin

from labelbox import pydantic_compat


class PromptText(ConfidenceMixin, CustomMetricsMixin, pydantic_compat.BaseModel):
    """ Prompt text for LLM data generation

    >>> PromptText(answer = "some text answer",
    >>>    confidence = 0.5,
    >>>    custom_metrics = [
    >>>     {
    >>>         "name": "iou",
    >>>         "value": 0.1
    >>>     }])
    """
    answer: str


class PromptClassificationAnnotation(BaseAnnotation, ConfidenceMixin,
                               CustomMetricsMixin):
    """Prompt annotation (non localized)

    >>> PromptClassificationAnnotation(
    >>>     value=PromptText(answer="my caption message"),
    >>>     feature_schema_id="my-feature-schema-id"
    >>> )

    Args:
        name (Optional[str])
        feature_schema_id (Optional[Cuid])
        value (Union[Text])
     """

    value: PromptText