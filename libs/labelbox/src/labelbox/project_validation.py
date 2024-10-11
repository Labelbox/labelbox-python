from typing import Annotated, Optional, Set

from pydantic import BaseModel, ConfigDict, Field, model_validator

from labelbox.schema.media_type import MediaType
from labelbox.schema.ontology_kind import EditorTaskType
from labelbox.schema.quality_mode import (
    BENCHMARK_AUTO_AUDIT_NUMBER_OF_LABELS,
    BENCHMARK_AUTO_AUDIT_PERCENTAGE,
    CONSENSUS_AUTO_AUDIT_NUMBER_OF_LABELS,
    CONSENSUS_AUTO_AUDIT_PERCENTAGE,
    QualityMode,
)

PositiveInt = Annotated[int, Field(gt=0)]


class _CoreProjectInput(BaseModel):
    name: str
    description: Optional[str] = None
    media_type: MediaType
    auto_audit_percentage: Optional[float] = None
    auto_audit_number_of_labels: Optional[int] = None
    quality_modes: Optional[Set[QualityMode]] = Field(
        default={QualityMode.Benchmark, QualityMode.Consensus}, exclude=True
    )
    is_benchmark_enabled: Optional[bool] = None
    is_consensus_enabled: Optional[bool] = None
    dataset_name_or_id: Optional[str] = None
    append_to_existing_dataset: Optional[bool] = None
    data_row_count: Optional[PositiveInt] = None
    editor_task_type: Optional[EditorTaskType] = None

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    @model_validator(mode="after")
    def validate_fields(self):
        if (
            self.auto_audit_percentage is not None
            or self.auto_audit_number_of_labels is not None
        ):
            raise ValueError(
                "quality_modes must be set instead of auto_audit_percentage or auto_audit_number_of_labels."
            )

        if not self.name.strip():
            raise ValueError("project name must be a valid string.")

        if self.quality_modes == {
            QualityMode.Benchmark,
            QualityMode.Consensus,
        }:
            self._set_quality_mode_attributes(
                CONSENSUS_AUTO_AUDIT_NUMBER_OF_LABELS,
                CONSENSUS_AUTO_AUDIT_PERCENTAGE,
                is_benchmark_enabled=True,
                is_consensus_enabled=True,
            )
        elif self.quality_modes == {QualityMode.Benchmark}:
            self._set_quality_mode_attributes(
                BENCHMARK_AUTO_AUDIT_NUMBER_OF_LABELS,
                BENCHMARK_AUTO_AUDIT_PERCENTAGE,
                is_benchmark_enabled=True,
            )
        elif self.quality_modes == {QualityMode.Consensus}:
            self._set_quality_mode_attributes(
                number_of_labels=CONSENSUS_AUTO_AUDIT_NUMBER_OF_LABELS,
                percentage=CONSENSUS_AUTO_AUDIT_PERCENTAGE,
                is_consensus_enabled=True,
            )

        if self.data_row_count is not None and self.data_row_count < 0:
            raise ValueError("data_row_count must be a positive integer.")

        return self

    def _set_quality_mode_attributes(
        self,
        number_of_labels,
        percentage,
        is_benchmark_enabled=False,
        is_consensus_enabled=False,
    ):
        self.auto_audit_number_of_labels = number_of_labels
        self.auto_audit_percentage = percentage
        self.is_benchmark_enabled = is_benchmark_enabled
        self.is_consensus_enabled = is_consensus_enabled
