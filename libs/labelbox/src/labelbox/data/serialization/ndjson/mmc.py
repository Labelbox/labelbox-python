from typing import Any, Dict, List, Optional, Union

from labelbox.utils import _CamelCaseMixin

from .base import _SubclassRegistryBase, DataRow, NDAnnotation
from ...annotation_types.mmc import (
    MessageSingleSelectionTask,
    MessageMultiSelectionTask,
    MessageRankingTask,
    MessageEvaluationTaskAnnotation,
)


class MessageTaskData(_CamelCaseMixin):
    format: str
    data: Union[
        MessageSingleSelectionTask,
        MessageMultiSelectionTask,
        MessageRankingTask,
    ]


class NDMessageTask(NDAnnotation, _SubclassRegistryBase):
    message_evaluation_task: MessageTaskData

    def to_common(self) -> MessageEvaluationTaskAnnotation:
        return MessageEvaluationTaskAnnotation(
            name=self.name,
            feature_schema_id=self.schema_id,
            value=self.message_evaluation_task.data,
            extra={"uuid": self.uuid},
        )

    @classmethod
    def from_common(
        cls,
        annotation: MessageEvaluationTaskAnnotation,
        data: Any,  # Union[ImageData, TextData],
    ) -> "NDMessageTask":
        return cls(
            uuid=str(annotation._uuid),
            name=annotation.name,
            schema_id=annotation.feature_schema_id,
            data_row=DataRow(id=data.uid, global_key=data.global_key),
            message_evaluation_task=MessageTaskData(
                format=annotation.value.format, data=annotation.value
            ),
        )
