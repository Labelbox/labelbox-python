import sys

from typing import Optional
if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict


class DataRowParams(TypedDict):
    include_data_row_details: Optional[bool]
    include_media_attributes: Optional[bool]
    include_metadata_fields: Optional[bool]
    include_attachments: Optional[bool]


class ProjectExportParams(DataRowParams):
    include_project_details: Optional[bool]
    include_label_details: Optional[bool]
    include_performance_details: Optional[bool]


class ModelRunExportParams(DataRowParams):
    # TODO: Add model run fields
    pass
