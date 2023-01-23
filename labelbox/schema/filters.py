import sys

if sys.version_info >= (3, 8):
    from typing import TypedDict, Optional
else:
    from typing_extensions import TypedDict, Optional


class DataRowFilter(TypedDict):
    data_row_details: Optional[bool]
    media_attributes: Optional[bool]
    metadata_fields: Optional[bool]
    attachments: Optional[bool]
    global_issues: Optional[bool]


class ProjectExportFilter(DataRowFilter):
    project_details: Optional[bool]
    label_details: Optional[bool]
    performance_details: Optional[bool]


class ModelRunExportFilter(DataRowFilter):
    # TODO: Add model run fields
    pass
