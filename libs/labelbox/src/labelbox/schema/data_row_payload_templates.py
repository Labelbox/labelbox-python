from typing import Dict, List

from pydantic import BaseModel, Field

from labelbox.schema.data_row import DataRowMetadataField


class ModelEvalutationTemlateRowData(BaseModel):
    type: str = Field(
        default="application/vnd.labelbox.conversational.model-chat-evaluation",
        frozen=True,
    )
    draft: bool = Field(default=True, frozen=True)
    rootMessageIds: List[str] = Field(default=[])
    actors: Dict = Field(default={})
    version: int = Field(default=2, frozen=True)
    messages: Dict = Field(default={})


class ModelEvaluationTemplate(BaseModel):
    row_data: ModelEvalutationTemlateRowData = Field(
        default=ModelEvalutationTemlateRowData()
    )
    attachments: List[Dict] = Field(default=[])
    embeddings: List[Dict] = Field(default=[])
    metadata_fields: List[DataRowMetadataField] = Field(default=[])
