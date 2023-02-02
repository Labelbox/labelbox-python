import sys

from typing import Optional

from pydantic import BaseModel


class DataRowParams(BaseModel):
    include_data_row_details: Optional[bool] = None
    include_media_attributes: Optional[bool] = None
    include_metadata_fields: Optional[bool] = None
    include_attachments: Optional[bool] = None


class ProjectExportParams(BaseModel):
    include_project_details: Optional[bool] = None
    include_label_details: Optional[bool] = None
    include_performance_details: Optional[bool] = None


class ModelRunExportParams(BaseModel):
    # TODO: Add model run fields
    pass
