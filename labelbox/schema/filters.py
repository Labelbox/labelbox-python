try:
    from typing import Optional
except:
    from typing_extensions import Optional

try:
    from typing import TypedDict
except:
    from typing_extensions import TypedDict


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
