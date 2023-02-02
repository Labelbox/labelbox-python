import sys

from typing import Optional

from pydantic import BaseModel


class DataRowParams(BaseModel):
    data_row_details: Optional[bool] = None
    media_attributes: Optional[bool] = None
    metadata_fields: Optional[bool] = None
    attachments: Optional[bool] = None


class ProjectExportParams(BaseModel):
    include_project_details: Optional[bool] = None
    include_label_details: Optional[bool] = None
    include_performance_details: Optional[bool] = None


class ModelRunExportParams(BaseModel):
    # TODO: Add model run fields
    pass
