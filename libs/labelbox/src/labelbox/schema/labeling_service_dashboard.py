from string import Template
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from labelbox.exceptions import ResourceNotFoundError
from labelbox.pagination import PaginatedCollection
from labelbox.pydantic_compat import BaseModel, root_validator, Field
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
    """
    Represent labeling service data for a project

    Attributes:
        id (str): project id
        name (str): project name
        status (LabelingServiceStatus): status of the labeling service
        tasks_completed (int): number of data rows completed
        tasks_remaining (int): number of data rows that have not started
        client (Any): labelbox client
    """
    id: str = Field(frozen=True)
    name: str = Field(frozen=True)
    service_type: Optional[str] = Field(frozen=True, default=None)
    created_at: Optional[datetime] = Field(frozen=True, default=None)
    updated_at: Optional[datetime] = Field(frozen=True, default=None)
    created_by_id: Optional[str] = Field(frozen=True, default=None)
    status: LabelingServiceStatus = Field(frozen=True,
                                          default=LabelingServiceStatus.Missing)
    data_rows_count: int = Field(frozen=True)
    data_rows_in_review_count: int = Field(frozen=True)
    data_rows_in_rework_count: int = Field(frozen=True)
    data_rows_done_count: int = Field(frozen=True)

    client: Any  # type Any to avoid circular import from client

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.client.enable_experimental:
            raise RuntimeError(
                "Please enable experimental in client to use LabelingService")

    @property
    def tasks_completed(self):
        return self.data_rows_done_count

    @property
    def tasks_remaining(self):
        return self.data_rows_count - self.data_rows_done_count

    class Config(_CamelCaseMixin.Config):
        ...

    @classmethod
    def get(cls, client, project_id: str) -> 'LabelingServiceDashboard':
        """
        Returns the labeling service associated with the project.

        Raises:
            ResourceNotFoundError: If the project does not have a labeling service.
        """
        query = f"""
                    query GetProjectByIdPyApi($id: ID!) {{
                    getProjectById(input: {{id: $id}}) {{
                        {GRAPHQL_QUERY_SELECTIONS}
                        }}
                    }}
                """
        result = client.execute(query, {"id": project_id}, experimental=True)
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

        params: Dict[str, Union[str, int]] = {}
        if after:
            params = {"from": after}

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
            experimental=True,
        )

    @root_validator(pre=True)
    def convert_boost_status_to_enum(cls, data):
        if 'boostStatus' in data:
            data['status'] = LabelingServiceStatus(data.pop('boostStatus'))

        return data
