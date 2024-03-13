import sys

from typing import Optional, Dict

from labelbox.schema.conflict_resolution_strategy import ConflictResolutionStrategy

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict


class SendToAnnotateFromCatalogParams(TypedDict):
    """
    Extra parameters for sending data rows and their predictions and/or annotations from Catalog to a specified project. 
    
    Note: 
        At least one of source_model_run_id or source_project_id must be provided.

    :param source_model_run_id: Optional[str] - The model run to use for sending predictions to a project. Defaults to None.
    :param predictions_ontology_mapping: Optional[Dict[str, str]] - A dict of feature schema ids to feature schema
        ids to map feature schemas from source model run's ontology to target project's ontology.
        Defaults to an empty dictionary.
    :param source_project_id: Optional[str] - The project to use for sending annotations to a project. Defaults to None.
    :param annotations_ontology_mapping: Optional[Dict[str, str]] - A dict of feature schema ids to feature schema
        ids to map feature schemas from source project's ontology to target project's ontology.
        Defaults to an empty dictionary.
    :param exclude_data_rows_in_project: Optional[bool] - Exclude data rows that are already in the project. Defaults
        to False.
    :param override_existing_annotations_rule: Optional[ConflictResolutionStrategy] - Strategy for resolving conflicts 
        between existing classifications in the project and incoming predictions/annotations. 
        Defaults to ConflictResolutionStrategy.KEEP_EXISTING.
    :param batch_priority: Optional[int] - The priority of the batch. Defaults to 5.
    """

    source_model_run_id: Optional[str]
    predictions_ontology_mapping: Optional[Dict[str, str]]
    source_project_id: Optional[str]
    annotations_ontology_mapping: Optional[Dict[str, str]]
    exclude_data_rows_in_project: Optional[bool]
    override_existing_annotations_rule: Optional[ConflictResolutionStrategy]
    batch_priority: Optional[int]


class SendToAnnotateFromModelParams(TypedDict):
    """
    Extra parameters for sending data rows and their predictions from a model run to a project. 
    
    Note: 
        At least one of source_model_run_id or source_project_id must be provided.

    :param predictions_ontology_mapping: Dict[str, str] - A dict of feature schema ids to feature schema
        ids to map feature schemas from source model run's ontology to target project's ontology.
        Defaults to an empty dictionary.
    :param exclude_data_rows_in_project: Optional[bool] - Exclude data rows that are already in the project. Defaults
        to False.
    :param override_existing_annotations_rule: Optional[ConflictResolutionStrategy] - Strategy for resolving conflicts 
        between existing classifications in the project and incoming predictions. 
        Defaults to ConflictResolutionStrategy.KEEP_EXISTING.
    :param batch_priority: Optional[int] - The priority of the batch. Defaults to 5.
    """

    predictions_ontology_mapping: Dict[str, str]
    exclude_data_rows_in_project: Optional[bool]
    override_existing_annotations_rule: Optional[ConflictResolutionStrategy]
    batch_priority: Optional[int]


def build_annotations_input(project_ontology_mapping: Optional[Dict[str, str]],
                            source_project_id: str):
    return {
        "projectId":
            source_project_id,
        "featureSchemaIdsMapping":
            project_ontology_mapping if project_ontology_mapping else {},
    }


def build_destination_task_queue_input(task_queue_id: str):
    destination_task_queue = {
        "type": "id",
        "value": task_queue_id
    } if task_queue_id else {
        "type": "done"
    }
    return destination_task_queue


def build_predictions_input(model_run_ontology_mapping: Optional[Dict[str,
                                                                      str]],
                            source_model_run_id: str):
    return {
        "featureSchemaIdsMapping":
            model_run_ontology_mapping if model_run_ontology_mapping else {},
        "modelRunId":
            source_model_run_id,
        "minConfidence":
            0,
        "maxConfidence":
            1
    }
