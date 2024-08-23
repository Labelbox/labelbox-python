from string import Template
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from labelbox.exceptions import ResourceNotFoundError
from labelbox.pagination import PaginatedCollection
from labelbox.pydantic_compat import BaseModel, root_validator, Field
from labelbox.schema.search_filters import SearchFilter, build_search_filter
from labelbox.utils import _CamelCaseMixin
from .ontology_kind import EditorTaskType
from labelbox.schema.media_type import MediaType
from labelbox.schema.labeling_service_status import LabelingServiceStatus
from labelbox.utils import _CamelCaseMixin, sentence_case

GRAPHQL_QUERY_SELECTIONS = """
                id
                name
                boostRequestedAt
                boostUpdatedAt
                boostRequestedBy
                boostStatus
                dataRowsCount
                dataRowsInReviewCount
                dataRowsInReworkCount
                dataRowsDoneCount
                mediaType
                editorTaskType
                tags
            """


class LabelingServiceDashboardTags(BaseModel):
    text: str
    color: str
    type: str


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
    created_at: Optional[datetime] = Field(frozen=True, default=None)
    updated_at: Optional[datetime] = Field(frozen=True, default=None)
    created_by_id: Optional[str] = Field(frozen=True, default=None)
    status: LabelingServiceStatus = Field(frozen=True, default=None)
    data_rows_count: int = Field(frozen=True)
    data_rows_in_review_count: int = Field(frozen=True)
    data_rows_in_rework_count: int = Field(frozen=True)
    data_rows_done_count: int = Field(frozen=True)
    media_type: Optional[MediaType] = Field(frozen=True, default=None)
    editor_task_type: EditorTaskType = Field(frozen=True, default=None)
    tags: List[LabelingServiceDashboardTags] = Field(frozen=True, default=None)

    client: Any  # type Any to avoid circular import from client

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.client.enable_experimental:
            raise RuntimeError(
                "Please enable experimental in client to use LabelingService")

    @property
    def tasks_completed(self):
        """
        Count how many data rows have been completed (i.e. in the Done queue)
        """
        return self.data_rows_done_count

    @property
    def tasks_remaining(self):
        """
        Count how many data rows have not been completed
        """
        return self.data_rows_count - self.data_rows_done_count

    @property
    def service_type(self):
        """
        Descriptive labeling service definition by media type and editor task type
        """
        if self.media_type is None:
            return None

        if self.editor_task_type is None:
            return sentence_case(self.media_type.value)

        if self.editor_task_type == EditorTaskType.OfflineModelChatEvaluation and self.media_type == MediaType.Conversational:
            return "Offline chat evaluation"

        if self.editor_task_type == EditorTaskType.ModelChatEvaluation and self.media_type == MediaType.Conversational:
            return "Live chat evaluation"

        if self.editor_task_type == EditorTaskType.ResponseCreation and self.media_type == MediaType.Text:
            return "Response creation"

        if self.media_type == MediaType.LLMPromptCreation or self.media_type == MediaType.LLMPromptResponseCreation:
            return "Prompt response creation"

        return sentence_case(self.media_type.value)

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
                message="The project does not have a labeling service data yet."
            )
        data = result["getProjectById"]
        data["client"] = client
        return cls(**data)

    @classmethod
    def get_all(
        cls,
        client,
        search_query: Optional[List[SearchFilter]] = None,
    ) -> PaginatedCollection:

        if search_query is not None:
            template = Template(
                """query SearchProjectsPyApi($$first: Int, $$from: String) {
                            searchProjects(input: {after: $$from, searchQuery: $search_query, size: $$first})
                                {
                                    nodes { $labeling_dashboard_selections }
                                    pageInfo { endCursor }
                                }
                            }
                        """)
        else:
            template = Template(
                """query SearchProjectsPyApi($$first: Int, $$from: String) {
                            searchProjects(input: {after: $$from, size: $$first})
                                {
                                    nodes { $labeling_dashboard_selections }
                                    pageInfo { endCursor }
                                }
                            }
                        """)
        query_str = template.substitute(
            labeling_dashboard_selections=GRAPHQL_QUERY_SELECTIONS,
            search_query=build_search_filter(search_query)
            if search_query else None,
        )
        params: Dict[str, Union[str, int]] = {}

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
    def convert_boost_data(cls, data):
        if 'boostStatus' in data:
            data['status'] = LabelingServiceStatus(data.pop('boostStatus'))

        if 'boostRequestedAt' in data:
            data['created_at'] = data.pop('boostRequestedAt')

        if 'boostUpdatedAt' in data:
            data['updated_at'] = data.pop('boostUpdatedAt')

        if 'boostRequestedBy' in data:
            data['created_by_id'] = data.pop('boostRequestedBy')

        return data

    def dict(self, *args, **kwargs):
        row = super().dict(*args, **kwargs)
        row.pop('client')
        row['tasks_completed'] = self.tasks_completed
        row['tasks_remaining'] = self.tasks_remaining
        row['service_type'] = self.service_type
        return row
