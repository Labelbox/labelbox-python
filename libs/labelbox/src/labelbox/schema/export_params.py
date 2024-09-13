import sys

from typing import Optional, List

EXPORT_LIMIT = 30

from labelbox.schema.media_type import MediaType

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict


class DataRowParams(TypedDict):
    data_row_details: Optional[bool]
    metadata_fields: Optional[bool]
    attachments: Optional[bool]
    embeddings: Optional[bool]
    media_type_override: Optional[MediaType]


class ProjectExportParams(DataRowParams):
    project_details: Optional[bool]
    label_details: Optional[bool]
    performance_details: Optional[bool]
    interpolated_frames: Optional[bool]


class CatalogExportParams(DataRowParams):
    project_details: Optional[bool]
    label_details: Optional[bool]
    performance_details: Optional[bool]
    model_run_ids: Optional[List[str]]
    project_ids: Optional[List[str]]
    interpolated_frames: Optional[bool]
    all_projects: Optional[bool]
    all_model_runs: Optional[bool]


class ModelRunExportParams(DataRowParams):
    predictions: Optional[bool]
    model_run_details: Optional[bool]


def _validate_array_length(array, max_length, array_name):
    if len(array) > max_length:
        raise ValueError(f"{array_name} cannot exceed {max_length} items")


def validate_catalog_export_params(params: CatalogExportParams):
    if "model_run_ids" in params and params["model_run_ids"] is not None:
        _validate_array_length(
            params["model_run_ids"], EXPORT_LIMIT, "model_run_ids"
        )

    if "project_ids" in params and params["project_ids"] is not None:
        _validate_array_length(
            params["project_ids"], EXPORT_LIMIT, "project_ids"
        )
