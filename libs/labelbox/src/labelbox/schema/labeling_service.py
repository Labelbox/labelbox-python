from datetime import datetime
from enum import Enum

from labelbox.data.annotation_types.types import Cuid
from labelbox.orm.db_object import experimental
from labelbox.pydantic_compat import BaseModel
from labelbox.utils import _CamelCaseMixin


class LabelingServiceStatus(Enum):
    Accepted = 'ACCEPTED',
    Calibration = 'CALIBRATION',
    Complete = 'COMPLETE',
    Production = 'PRODUCTION',
    Requested = 'REQUESTED',
    SetUp = 'SET_UP'


@experimental
class LabelingService(_CamelCaseMixin, BaseModel):
    id: Cuid
    project_id: Cuid
    created_at: datetime
    updated_at: datetime
    created_by_id: Cuid
    status: LabelingServiceStatus

    def status_as_string(self):
        return self.status.value
