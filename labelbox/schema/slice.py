from typing import Optional, List
from labelbox.exceptions import ResourceNotFoundError
from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Entity, Field
from labelbox.pagination import PaginatedCollection
from labelbox.schema.export_params import CatalogExportParams, validate_catalog_export_params
from labelbox.schema.task import Task
from labelbox.schema.user import User


class Slice(DbObject):
    """
    A Slice is a saved set of filters (saved query).
    This is an abstract class and should not be instantiated.

    Attributes:
        name (datetime)
        description (datetime)
        created_at (datetime)
        updated_at (datetime)
        filter (json)
    """

    name = Field.String("name")
    description = Field.String("description")
    created_at = Field.DateTime("created_at")
    updated_at = Field.DateTime("updated_at")
    filter = Field.Json("filter")


class CatalogSlice(Slice):
    """
    Represents a Slice used for filtering data rows in Catalog.
    """

    def get_data_row_ids(self) -> PaginatedCollection:
        """
        Fetches all data row ids that match this Slice

        Returns:
            A PaginatedCollection of data row ids
        """
        query_str = """
            query getDataRowIdsBySavedQueryPyApi($id: ID!, $from: String, $first: Int!) {
                getDataRowIdsBySavedQuery(input: {
                    savedQueryId: $id,
                    after: $from
                    first: $first
                }) {
                    totalCount
                    nodes
                    pageInfo {
                        endCursor
                        hasNextPage
                    }
                }
            }
        """
        return PaginatedCollection(
            client=self.client,
            query=query_str,
            params={'id': self.uid},
            dereferencing=['getDataRowIdsBySavedQuery', 'nodes'],
            obj_class=lambda _, data_row_id: data_row_id,
            cursor_path=['getDataRowIdsBySavedQuery', 'pageInfo', 'endCursor'])

    def export_v2(self,
                  task_name: Optional[str] = None,
                  params: Optional[CatalogExportParams] = None) -> Task:
        """
        Creates a slice export task with the given params and returns the task.
        >>>     slice = client.get_catalog_slice("SLICE_ID")
        >>>     task = slice.export_v2(
        >>>         params={"performance_details": False, "label_details": True}
        >>>     )
        >>>     task.wait_till_done()
        >>>     task.result
        """

        _params = params or CatalogExportParams({
            "attachments": False,
            "metadata_fields": False,
            "data_row_details": False,
            "project_details": False,
            "performance_details": False,
            "label_details": False,
            "media_type_override": None,
            "model_run_ids": None,
            "project_ids": None,
            "interpolated_frames": False,
        })
        validate_catalog_export_params(_params)

        mutation_name = "exportDataRowsInSlice"
        create_task_query_str = """mutation exportDataRowsInSlicePyApi($input: ExportDataRowsInSliceInput!){
          %s(input: $input) {taskId} }
          """ % (mutation_name)

        media_type_override = _params.get('media_type_override', None)
        query_params = {
            "input": {
                "taskName": task_name,
                "filters": {
                    "sliceId": self.uid
                },
                "params": {
                    "mediaTypeOverride":
                        media_type_override.value
                        if media_type_override is not None else None,
                    "includeAttachments":
                        _params.get('attachments', False),
                    "includeMetadata":
                        _params.get('metadata_fields', False),
                    "includeDataRowDetails":
                        _params.get('data_row_details', False),
                    "includeProjectDetails":
                        _params.get('project_details', False),
                    "includePerformanceDetails":
                        _params.get('performance_details', False),
                    "includeLabelDetails":
                        _params.get('label_details', False),
                    "includeInterpolatedFrames":
                        _params.get('interpolated_frames', False),
                    "projectIds":
                        _params.get('project_ids', None),
                    "modelRunIds":
                        _params.get('model_run_ids', None),
                },
            }
        }

        res = self.client.execute(
            create_task_query_str,
            query_params,
        )
        res = res[mutation_name]
        task_id = res["taskId"]
        user: User = self.client.get_user()
        tasks: List[Task] = list(
            user.created_tasks(where=Entity.Task.uid == task_id))
        # Cache user in a private variable as the relationship can't be
        # resolved due to server-side limitations (see Task.created_by)
        # for more info.
        if len(tasks) != 1:
            raise ResourceNotFoundError(Entity.Task, task_id)
        task: Task = tasks[0]
        task._user = user
        return task


class ModelSlice(Slice):
    """
    Represents a Slice used for filtering data rows in Model.
    """

    def get_data_row_ids(self) -> PaginatedCollection:
        """
        Fetches all data row ids that match this Slice

        Returns:
            A PaginatedCollection of data row ids
        """
        query_str = """
            query getDataRowIdsBySavedQueryPyApi($id: ID!, $from: String, $first: Int!) {
                getDataRowIdsBySavedQuery(input: {
                    savedQueryId: $id,
                    after: $from
                    first: $first
                }) {
                    totalCount
                    nodes
                    pageInfo {
                        endCursor
                        hasNextPage
                    }
                }
            }
        """
        return PaginatedCollection(
            client=self.client,
            query=query_str,
            params={'id': self.uid},
            dereferencing=['getDataRowIdsBySavedQuery', 'nodes'],
            obj_class=lambda _, data_row_id: data_row_id,
            cursor_path=['getDataRowIdsBySavedQuery', 'pageInfo', 'endCursor'])
