import sys

from typing import Optional, Dict

from labelbox.schema.conflict_resolution_strategy import ConflictResolutionStrategy

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict


class SendToAnnotateFromCatalogParams(TypedDict):
    """
    Extra parameters for sending data rows to a project through catalog. At least one of source_model_run_id or
    source_project_id must be provided.

    :param source_model_run_id: Optional[str] - The model run to use for predictions. Defaults to None.
    :param model_run_ontology_mapping: Optional[Dict[str, str]] - A mapping of ontology ids to ontology ids. Defaults to
        an empty dictionary.
    :param source_project_id: Optional[str] - The project to use for predictions. Defaults to None.
    :param project_ontology_mapping: Optional[Dict[str, str]] - A mapping of ontology ids to ontology ids. Defaults to
        an empty dictionary.
    :param exclude_data_rows_in_project: Optional[bool] - Exclude data rows that are already in the project. Defaults
        to False.
    :param override_existing_annotations_rule: Optional[ConflictResolutionStrategy] - The strategy defining how to
        handle conflicts in classifications between the data rows that already exist in the project and incoming
        predictions from the source model run or annotations from the source project. Defaults to
        ConflictResolutionStrategy.SKIP.
    :param batch_priority: Optional[int] - The priority of the batch. Defaults to 5.
    """

    source_model_run_id: Optional[str]
    model_run_ontology_mapping: Optional[Dict[str, str]]
    source_project_id: Optional[str]
    project_ontology_mapping: Optional[Dict[str, str]]
    exclude_data_rows_in_project: Optional[bool]
    override_existing_annotations_rule: Optional[ConflictResolutionStrategy]
    batch_priority: Optional[int]


class SendToAnnotateFromModelParams(TypedDict):
    """
    Extra parameters for sending data rows to a project through a model run.

    :param model_run_ontology_mapping: Dict[str, str] - A mapping of ontology ids to ontology ids. Defaults to an empty
        dictionary.
    :param exclude_data_rows_in_project: Optional[bool] - Exclude data rows that are already in the project. Defaults
        to False.
    :param override_existing_annotations_rule: Optional[ConflictResolutionStrategy] - The strategy defining how to
        handle conflicts in classifications between the data rows that already exist in the project and incoming
        predictions from the source model run. Defaults to ConflictResolutionStrategy.SKIP.
    :param batch_priority: Optional[int] - The priority of the batch. Defaults to 5.
    """

    model_run_ontology_mapping: Dict[str, str]
    exclude_data_rows_in_project: Optional[bool]
    override_existing_annotations_rule: Optional[ConflictResolutionStrategy]
    batch_priority: Optional[int]
