from datetime import datetime
from typing import Any

from labelbox.exceptions import ResourceNotFoundError
from labelbox.pydantic_compat import BaseModel
from labelbox.utils import _CamelCaseMixin
from labelbox.schema.labeling_service import LabelingServiceStatus


class LabelingServiceDashboard(BaseModel):
    project_id: str
    project_name: str
    service_type: str
    created_at: datetime
    updated_at: datetime
    created_by_id: str
    status: LabelingServiceStatus
    tasks_completed: int
    tasks_remaining: int

    client: Any  # type Any to avoid circular import from client

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.client.enable_experimental:
            raise RuntimeError(
                "Please enable experimental in client to use LabelingService")

    class Config(_CamelCaseMixin.Config):
        ...

    @classmethod
    def get(cls, client, project_id: str) -> 'LabelingServiceDashboard':
        """
        Returns the labeling service associated with the project.

        Raises:
            ResourceNotFoundError: If the project does not have a labeling service.
        """
        query = """
            query GetProjectByIdPyApi($projectId: ID!) {
            getProjectById(data: { projectId: $projectId }) {
                    projectId
                    projectName
                    serviceType
                    createdAt
                    updatedAt
                    createdById
                    status
                    tasksCompleted
                    tasksRemaining
                }
            }
        """
        result = client.execute(query, {"projectId": project_id})
        if result["getProjectById"] is None:
            raise ResourceNotFoundError(
                message="The project does not have a labeling service.")
        data = result["getProjectById"]
        data["client"] = client
        return cls(**data)
