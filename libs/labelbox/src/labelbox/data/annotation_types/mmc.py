from abc import ABC
from typing import ClassVar, List, Union

from pydantic import ConfigDict, field_validator

from labelbox.utils import _CamelCaseMixin
from labelbox.data.annotation_types.annotation import BaseAnnotation


class MessageInfo(_CamelCaseMixin):
    message_id: str
    model_config_name: str

    model_config = ConfigDict(protected_namespaces=())


class OrderedMessageInfo(MessageInfo):
    order: int


class _BaseMessageEvaluationTask(_CamelCaseMixin, ABC):
    format: ClassVar[str]
    parent_message_id: str

    model_config = ConfigDict(protected_namespaces=())


class MessageSingleSelectionTask(_BaseMessageEvaluationTask, MessageInfo):
    format: ClassVar[str] = "message-single-selection"


class MessageMultiSelectionTask(_BaseMessageEvaluationTask):
    format: ClassVar[str] = "message-multi-selection"
    selected_messages: List[MessageInfo]


class MessageRankingTask(_BaseMessageEvaluationTask):
    format: ClassVar[str] = "message-ranking"
    ranked_messages: List[OrderedMessageInfo]

    @field_validator("ranked_messages")
    def _validate_ranked_messages(cls, v: List[OrderedMessageInfo]):
        if not {msg.order for msg in v} == set(range(1, len(v) + 1)):
            raise ValueError(
                "Messages must be ordered by unique and consecutive natural numbers starting from 1"
            )
        return v


class MessageEvaluationTaskAnnotation(BaseAnnotation):
    value: Union[
        MessageSingleSelectionTask,
        MessageMultiSelectionTask,
        MessageRankingTask,
    ]
