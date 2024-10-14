from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from labelbox.schema.data_row import DataRowMetadataField


class ModelEvalutationTemplateRowData(BaseModel):
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
    """
    Use this class to create a model evaluation data row.

    Examples:
        >>> data = ModelEvaluationTemplate()
        >>> data.row_data.rootMessageIds = ["root1"]
        >>> vector = [random.uniform(1.0, 2.0) for _ in range(embedding.dims)]
        >>> data.embeddings = [...]
        >>> data.metadata_fields = [...]
        >>> data.attachments = [...]
        >>> content = data.model_dump()
        >>> task = dataset.create_data_rows([content])
    """

    row_data: ModelEvalutationTemplateRowData = Field(
        default=ModelEvalutationTemplateRowData()
    )
    global_key: Optional[str] = None
    attachments: List[Dict] = Field(default=[])
    embeddings: List[Dict] = Field(default=[])
    metadata_fields: List[DataRowMetadataField] = Field(default=[])
