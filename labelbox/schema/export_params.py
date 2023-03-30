import sys

from typing import Optional, List

from labelbox.schema.media_type import MediaType
if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict


class DataRowParams(TypedDict):
    data_row_details: Optional[bool]
    metadata_fields: Optional[bool]
    attachments: Optional[bool]
    media_type_override: Optional[MediaType]


class ProjectExportParams(DataRowParams):
    project_details: Optional[bool]
    label_details: Optional[bool]
    performance_details: Optional[bool]


class CatalogExportParams(DataRowParams):
    project_details: Optional[bool]
    label_details: Optional[bool]
    performance_details: Optional[bool]
    model_run_ids: Optional[List[str]]
    project_ids: Optional[List[str]]
    pass


class ModelRunExportParams(DataRowParams):
    # TODO: Add model run fields
    pass
