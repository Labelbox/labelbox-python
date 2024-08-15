from datetime import datetime
from string import Template
from typing import Any, Dict, List, Optional

from labelbox.exceptions import ResourceNotFoundError
from labelbox.orm.comparison import Comparison
from labelbox.orm import query
from ..orm.model import Field
from labelbox.pagination import PaginatedCollection
from labelbox.pydantic_compat import BaseModel, root_validator
from .organization import Organization
from labelbox.utils import _CamelCaseMixin
from labelbox.schema.labeling_service_status import LabelingServiceStatus

GRAPHQL_QUERY_SELECTIONS = """
                id
                name
                # serviceType
                # createdAt
                # updatedAt
                # createdById
                boostStatus
                dataRowsCount
                dataRowsInReviewCount
                dataRowsInReworkCount
                dataRowsDoneCount
            """


class LabelingServiceDashboard(BaseModel):
    id: str
    name: str
    # service_type: str
    # created_at: datetime
    # updated_at: datetime
    # created_by_id: str
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
            query GetProjectByIdPyApi($id: ID!) {
            getProjectById(input: {id: $id}) {
                    id
                    name
                    # serviceType
                    # createdAt
                    # updatedAt
                    # createdById
                    boostStatus
                    dataRowsCount
                    dataRowsInReviewCount
                    dataRowsInReworkCount
                    dataRowsDoneCount
                }
            }
        """
        result = client.execute(query, {"id": project_id})
        if result["getProjectById"] is None:
            raise ResourceNotFoundError(
                message="The project does not have a labeling service.")
        data = result["getProjectById"]
        data["client"] = client
        return cls(**data)

    @classmethod
    def get_all(
        cls,
        client,
        after: Optional[str] = None,
        # where: Optional[Comparison] = None,
        search_query: Optional[List[Dict]] = None,
    ) -> PaginatedCollection:
        template = Template(
            """query SearchProjectsPyApi($$first: Int, $$from: String) {
                        searchProjects(input: {after: $$from, searchQuery: $search_query, size: $$first})
                            {
                                nodes { $labeling_dashboard_selections }
                                pageInfo { endCursor }
                            }
                        }
                    """)
        organization_id = client.get_organization().uid
        query_str = template.substitute(
            labeling_dashboard_selections=GRAPHQL_QUERY_SELECTIONS,
            search_query=
            f"[{{type: \"organization\", operator: \"is\",  values: [\"{organization_id}\"]}}]"
        )

        params = {
            'from': after,
        }

        def convert_to_labeling_service_dashboard(client, data):
            data['client'] = client
            return LabelingServiceDashboard(**data)

        return PaginatedCollection(
            client=client,
            query=query_str,
            params=params,
            dereferencing=['searchProjects', 'nodes'],
            obj_class=convert_to_labeling_service_dashboard,
            cursor_path=['searchProjects', 'pageInfo', 'endCursor'],
        )

    @root_validator(pre=True)
    def convert_graphql_to_attrs(cls, data):
        if 'boostStatus' in data:
            data['status'] = LabelingServiceStatus(data.pop('boostStatus'))
        if 'dataRowsDoneCount' in data:
            data['tasksCompleted'] = data.pop('dataRowsDoneCount')
        if 'dataRowsCount' in data and 'dataRowsInReviewCount' in data and 'dataRowsInReworkCount' in data:
            data['tasksRemaining'] = data['dataRowsCount'] - (
                data['dataRowsInReviewCount'] + data['dataRowsInReworkCount'])

        return data
