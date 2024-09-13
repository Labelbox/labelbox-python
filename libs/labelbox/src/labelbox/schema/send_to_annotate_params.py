import sys

from typing import Optional, Dict

from labelbox.schema.conflict_resolution_strategy import (
    ConflictResolutionStrategy,
)

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

from pydantic import BaseModel, model_validator


class SendToAnnotateFromCatalogParams(BaseModel):
    """
    Extra parameters for sending data rows to a project through catalog. At least one of source_model_run_id or
    source_project_id must be provided.

    :param source_model_run_id: Optional[str] - The model run to use for predictions. Defaults to None.
    :param predictions_ontology_mapping: Optional[Dict[str, str]] - A mapping of feature schema ids to feature schema
        ids. Defaults to an empty dictionary.
    :param source_project_id: Optional[str] - The project to use for predictions. Defaults to None.
    :param annotations_ontology_mapping: Optional[Dict[str, str]] - A mapping of feature schema ids to feature schema
        ids. Defaults to an empty dictionary.
    :param exclude_data_rows_in_project: Optional[bool] - Exclude data rows that are already in the project. Defaults
        to False.
    :param override_existing_annotations_rule: Optional[ConflictResolutionStrategy] - The strategy defining how to
        handle conflicts in classifications between the data rows that already exist in the project and incoming
        predictions from the source model run or annotations from the source project. Defaults to
        ConflictResolutionStrategy.KEEP_EXISTING.
    :param batch_priority: Optional[int] - The priority of the batch. Defaults to 5.
    """

    source_model_run_id: Optional[str] = None
    source_project_id: Optional[str] = None
    predictions_ontology_mapping: Optional[Dict[str, str]] = {}
    annotations_ontology_mapping: Optional[Dict[str, str]] = {}
    exclude_data_rows_in_project: Optional[bool] = False
    override_existing_annotations_rule: Optional[ConflictResolutionStrategy] = (
        ConflictResolutionStrategy.KeepExisting
    )
    batch_priority: Optional[int] = 5

    @model_validator(mode="after")
    def check_project_id_or_model_run_id(self):
        if not self.source_model_run_id and not self.source_project_id:
            raise ValueError(
                "Either source_project_id or source_model_id are required"
            )
        if self.source_model_run_id and self.source_project_id:
            raise ValueError(
                "Provide only a source_project_id or source_model_id not both"
            )
        return self


class SendToAnnotateFromModelParams(TypedDict):
    """
    Extra parameters for sending data rows to a project through a model run.

    :param predictions_ontology_mapping: Dict[str, str] - A mapping of feature schema ids to feature schema ids.
        Defaults to an empty dictionary.
    :param exclude_data_rows_in_project: Optional[bool] - Exclude data rows that are already in the project. Defaults
        to False.
    :param override_existing_annotations_rule: Optional[ConflictResolutionStrategy] - The strategy defining how to
        handle conflicts in classifications between the data rows that already exist in the project and incoming
        predictions from the source model run. Defaults to ConflictResolutionStrategy.KEEP_EXISTING.
    :param batch_priority: Optional[int] - The priority of the batch. Defaults to 5.
    """

    predictions_ontology_mapping: Dict[str, str]
    exclude_data_rows_in_project: Optional[bool]
    override_existing_annotations_rule: Optional[ConflictResolutionStrategy]
    batch_priority: Optional[int]


def build_annotations_input(
    project_ontology_mapping: Optional[Dict[str, str]], source_project_id: str
):
    return {
        "projectId": source_project_id,
        "featureSchemaIdsMapping": project_ontology_mapping
        if project_ontology_mapping
        else {},
    }


def build_destination_task_queue_input(task_queue_id: str):
    destination_task_queue = (
        {"type": "id", "value": task_queue_id}
        if task_queue_id
        else {"type": "done"}
    )
    return destination_task_queue


def build_predictions_input(
    model_run_ontology_mapping: Optional[Dict[str, str]],
    source_model_run_id: str,
):
    return {
        "featureSchemaIdsMapping": model_run_ontology_mapping
        if model_run_ontology_mapping
        else {},
        "modelRunId": source_model_run_id,
        "minConfidence": 0,
        "maxConfidence": 1,
    }
