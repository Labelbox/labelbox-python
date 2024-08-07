from datetime import datetime
from enum import Enum
from typing import Any
from typing_extensions import Annotated

from labelbox.exceptions import ResourceNotFoundError

from labelbox.pydantic_compat import BaseModel, Field
from labelbox.utils import _CamelCaseMixin

Cuid = Annotated[str, Field(min_length=25, max_length=25)]


class LabelingServiceStatus(Enum):
    Accepted = 'ACCEPTED'
    Calibration = 'CALIBRATION'
    Complete = 'COMPLETE'
    Production = 'PRODUCTION'
    Requested = 'REQUESTED'
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
        Starts the labeling service for the project. This is equivalent to a UI action to Request Specialized Labelers

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

    def request(self) -> 'LabelingService':
        """
        Creates a request to labeling service to start labeling for the project. 
        Our back end will validate that the project is ready for labeling and then request the labeling service.

        Returns:
            LabelingService: The labeling service for the project.
        Raises:
            ResourceNotFoundError: If ontology is not associated with the project
                or if any projects required prerequisites are missing.

        """

        query_str = """mutation ValidateAndRequestProjectBoostWorkforcePyApi($projectId: ID!) {
            validateAndRequestProjectBoostWorkforce(
                data: { projectId: $projectId }
            ) {
                success
            }
        }
        """
        result = self.client.execute(query_str, {"projectId": self.project_id},
                                     raise_return_resource_not_found=True)
        success = result["validateAndRequestProjectBoostWorkforce"]["success"]
        if not success:
            raise Exception("Failed to start labeling service")
        return LabelingService.get(self.client, self.project_id)

    @classmethod
    def getOrCreate(cls, client, project_id: Cuid) -> 'LabelingService':
        """
        Returns the labeling service associated with the project. If the project does not have a labeling service, it will create one.

        Returns:
            LabelingService: The labeling service for the project.
        """
        try:
            return cls.get(client, project_id)
        except ResourceNotFoundError:
            return cls.start(client, project_id)

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
