import sys

from typing import Optional
if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict


class DataRowParams(TypedDict):
    data_row_details: Optional[bool]
    media_attributes: Optional[bool]
    metadata_fields: Optional[bool]
    attachments: Optional[bool]


class ProjectExportParams(DataRowParams):
    project_details: Optional[bool]
    labels: Optional[bool]
    performance_details: Optional[bool]


class ModelRunExportParams(DataRowParams):
    # TODO: Add model run fields
    pass
