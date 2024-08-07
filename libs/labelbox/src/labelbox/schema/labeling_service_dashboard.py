from datetime import datetime
from string import Template
from typing import Any, Optional

from labelbox.exceptions import ResourceNotFoundError
from labelbox.orm.comparison import Comparison
from labelbox.pagination import PaginatedCollection
from labelbox.pydantic_compat import BaseModel, root_validator
from labelbox.utils import _CamelCaseMixin
from labelbox.schema.labeling_service_status import LabelingServiceStatus


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
        from_cursor: Optional[str] = None,
        where: Optional[Comparison] = None,
    ) -> PaginatedCollection:
        page_size = 500  # hardcode to avoid overloading the server
        # where_param = query.where_as_dict(Entity.DataRow,
        #                                   where) if where is not None else None

        template = Template(
            """query SearchProjectsPyApi($$id: ID!, $$after: ID, $$first: Int, $$where: SearchProjectsInput)  {
                        searchProjects(id: $$id, after: $$after, first: $$first, where: $$where)
                            {
                                nodes { $datarow_selections }
                                pageInfo { hasNextPage startCursor }
                            }
                        }
                    """)
        query_str = template.substitute(
            datarow_selections=LabelingServiceDashboard.schema()
            ['properties'].keys())

        params = {
            'id': self.uid,
            'from': from_cursor,
            'first': page_size,
            'where': where_param,
        }

        return PaginatedCollection(
            client=client,
            query=query_str,
            params=params,
            dereferencing=['searchProjects', 'nodes'],
            obj_class=LabelingServiceDashboard,
            cursor_path=['datasetDataRows', 'pageInfo', 'endCursor'],
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
