from datetime import datetime
from enum import Enum

from ..client import Client
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

    @classmethod
    def start(cls, client: Client, project_id: Cuid) -> 'LabelingService':
        return cls._create(client=client, project_id=project_id)

"""
mutation CreateProjectBoostWorkforce($projectId: ID!) {
  upsertProjectBoostWorkforce(data: { projectId: $projectId }) {
    success
    __typename
  }
}
{
  "projectId": "clz0b7jg901fh07zic3u67b7g"
}


{
  "data": {
    "upsertProjectBoostWorkforce": {
      "success": true,
      "__typename": "ProjectBoostWorkforceResult"
    }
  }
}
"""
    @classmethod
    def _create(cls, client: Client, project_id: Cuid) -> 'LabelingService':
        ...
    
    def status_as_string(self):
        return self.status.value
