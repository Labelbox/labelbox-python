from datetime import datetime
from enum import Enum
from typing import Any

from labelbox.exceptions import ResourceNotFoundError

from labelbox.data.annotation_types.types import Cuid
from labelbox.pydantic_compat import BaseModel
from labelbox.utils import _CamelCaseMixin


class LabelingServiceStatus(Enum):
    Accepted = 'ACCEPTED',
    Calibration = 'CALIBRATION',
    Complete = 'COMPLETE',
    Production = 'PRODUCTION',
    Requested = 'REQUESTED',
    SetUp = 'SET_UP'


class LabelingService(BaseModel):
    id: Cuid
    project_id: Cuid
    created_at: datetime
    updated_at: datetime
    created_by_id: Cuid
    status: LabelingServiceStatus
    client: Any  # type Any to avoid circular import from client

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.client.enable_experimental:
            raise RuntimeError(
                "Please enable experimental in client to use LabelingService")

    class Config(_CamelCaseMixin.Config):
        ...

    @classmethod
    def start(cls, client, project_id: Cuid) -> 'LabelingService':
        """
        Starts the labeling service for the project. This is equivalent to a UI acction to Request Specialized Labelers

        Returns:
            LabelingService: The labeling service for the project.
        Raises:
            Exception: If the service fails to start.
        """
        query_str = """mutation CreateProjectBoostWorkforcePyApi($projectId: ID!) {
          upsertProjectBoostWorkforce(data: { projectId: $projectId }) {
            success
          }
        }"""
        result = client.execute(query_str, {"projectId": project_id})
        success = result["upsertProjectBoostWorkforce"]["success"]
        if not success:
            raise Exception("Failed to start labeling service")
        return cls.get(client, project_id)

    @classmethod
    def get(cls, client, project_id: Cuid) -> 'LabelingService':
        """
        Returns the labeling service associated with the project.

        Raises:
            ResourceNotFoundError: If the project does not have a labeling service.
        """
        query = """
            query GetProjectBoostWorkforcePyApi($projectId: ID!) {
            projectBoostWorkforce(data: { projectId: $projectId }) {
                    id
                    projectId
                    createdAt
                    updatedAt
                    createdById
                    status
                }
            }
        """
        result = client.execute(query, {"projectId": project_id})
        if result["projectBoostWorkforce"] is None:
            raise ResourceNotFoundError(
                message="The project does not have a labeling service.")
        data = result["projectBoostWorkforce"]
        data["client"] = client
        return LabelingService(**data)
