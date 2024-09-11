from dataclasses import dataclass
from typing import Optional, Tuple, Union
import warnings
from labelbox.orm.db_object import DbObject, experimental
from labelbox.orm.model import Field
from labelbox.pagination import PaginatedCollection
from labelbox.schema.export_params import (
    CatalogExportParams,
    validate_catalog_export_params,
)
from labelbox.schema.export_task import ExportTask
from labelbox.schema.identifiable import GlobalKey, UniqueId
from labelbox.schema.task import Task


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

    @dataclass
    class DataRowIdAndGlobalKey:
        id: UniqueId
        global_key: Optional[GlobalKey]

        def __init__(self, id: str, global_key: Optional[str]):
            self.id = UniqueId(id)
            self.global_key = GlobalKey(global_key) if global_key else None

        def to_hash(self):
            return {
                "id": self.id.key,
                "global_key": self.global_key.key if self.global_key else None,
            }


class CatalogSlice(Slice):
    """
    Represents a Slice used for filtering data rows in Catalog.
    """

    def get_data_row_ids(self) -> PaginatedCollection:
        """
        Fetches all data row ids that match this Slice

        Returns:
            A PaginatedCollection of mapping of data row ids to global keys
        """

        warnings.warn(
            "get_data_row_ids will be deprecated. Use get_data_row_identifiers instead"
        )

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
            params={"id": str(self.uid)},
            dereferencing=["getDataRowIdsBySavedQuery", "nodes"],
            obj_class=lambda _, data_row_id: data_row_id,
            cursor_path=["getDataRowIdsBySavedQuery", "pageInfo", "endCursor"],
        )

    def get_data_row_identifiers(self) -> PaginatedCollection:
        """
        Fetches all data row ids and global keys (where defined) that match this Slice

        Returns:
            A PaginatedCollection of Slice.DataRowIdAndGlobalKey
        """
        query_str = """
            query getDataRowIdenfifiersBySavedQueryPyApi($id: ID!, $from: String, $first: Int!) {
                getDataRowIdentifiersBySavedQuery(input: {
                    savedQueryId: $id,
                    after: $from
                    first: $first
                }) {
                    totalCount
                    nodes
                    {
                        id
                        globalKey
                    }
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
            params={"id": str(self.uid)},
            dereferencing=["getDataRowIdentifiersBySavedQuery", "nodes"],
            obj_class=lambda _, data_row_id_and_gk: Slice.DataRowIdAndGlobalKey(
                data_row_id_and_gk.get("id"),
                data_row_id_and_gk.get("globalKey", None),
            ),
            cursor_path=[
                "getDataRowIdentifiersBySavedQuery",
                "pageInfo",
                "endCursor",
            ],
        )

    def export(
        self,
        task_name: Optional[str] = None,
        params: Optional[CatalogExportParams] = None,
    ) -> ExportTask:
        """
        Creates a slice export task with the given params and returns the task.
        >>>     slice = client.get_catalog_slice("SLICE_ID")
        >>>     task = slice.export(
        >>>         params={"performance_details": False, "label_details": True}
        >>>     )
        >>>     task.wait_till_done()
        >>>     task.result
        """
        task, _ = self._export(task_name, params, streamable=True)
        return ExportTask(task)

    def export_v2(
        self,
        task_name: Optional[str] = None,
        params: Optional[CatalogExportParams] = None,
    ) -> Union[Task, ExportTask]:
        """
        Creates a slice export task with the given params and returns the task.
        >>>     slice = client.get_catalog_slice("SLICE_ID")
        >>>     task = slice.export_v2(
        >>>         params={"performance_details": False, "label_details": True}
        >>>     )
        >>>     task.wait_till_done()
        >>>     task.result
        """
        task, is_streamable = self._export(task_name, params)
        if is_streamable:
            return ExportTask(task, True)
        return task

    def _export(
        self,
        task_name: Optional[str] = None,
        params: Optional[CatalogExportParams] = None,
        streamable: bool = False,
    ) -> Tuple[Task, bool]:
        _params = params or CatalogExportParams(
            {
                "attachments": False,
                "embeddings": False,
                "metadata_fields": False,
                "data_row_details": False,
                "project_details": False,
                "performance_details": False,
                "label_details": False,
                "media_type_override": None,
                "model_run_ids": None,
                "project_ids": None,
                "interpolated_frames": False,
                "all_projects": False,
                "all_model_runs": False,
            }
        )
        validate_catalog_export_params(_params)

        mutation_name = "exportDataRowsInSlice"
        create_task_query_str = (
            f"mutation {mutation_name}PyApi"
            f"($input: ExportDataRowsInSliceInput!)"
            f"{{{mutation_name}(input: $input){{taskId isStreamable}}}}"
        )

        media_type_override = _params.get("media_type_override", None)
        query_params = {
            "input": {
                "taskName": task_name,
                "filters": {"sliceId": self.uid},
                "isStreamableReady": True,
                "params": {
                    "mediaTypeOverride": media_type_override.value
                    if media_type_override is not None
                    else None,
                    "includeAttachments": _params.get("attachments", False),
                    "includeEmbeddings": _params.get("embeddings", False),
                    "includeMetadata": _params.get("metadata_fields", False),
                    "includeDataRowDetails": _params.get(
                        "data_row_details", False
                    ),
                    "includeProjectDetails": _params.get(
                        "project_details", False
                    ),
                    "includePerformanceDetails": _params.get(
                        "performance_details", False
                    ),
                    "includeLabelDetails": _params.get("label_details", False),
                    "includeInterpolatedFrames": _params.get(
                        "interpolated_frames", False
                    ),
                    "projectIds": _params.get("project_ids", None),
                    "modelRunIds": _params.get("model_run_ids", None),
                    "allProjects": _params.get("all_projects", False),
                    "allModelRuns": _params.get("all_model_runs", False),
                },
                "streamable": streamable,
            }
        }

        res = self.client.execute(
            create_task_query_str, query_params, error_log_key="errors"
        )
        res = res[mutation_name]
        task_id = res["taskId"]
        is_streamable = res["isStreamable"]
        return Task.get_task(self.client, task_id), is_streamable


class ModelSlice(Slice):
    """
    Represents a Slice used for filtering data rows in Model.
    """

    @classmethod
    def query_str(cls):
        query_str = """
        query getDataRowIdenfifiersBySavedModelQueryPyApi($id: ID!, $modelRunId: ID, $from: DataRowIdentifierCursorInput, $first: Int!) {
            getDataRowIdentifiersBySavedModelQuery(input: {
                savedQueryId: $id,
                modelRunId: $modelRunId,
                after: $from
                first: $first
            }) {
                totalCount
                nodes
                {
                    id
                    globalKey
                }
                pageInfo {
                    endCursor {
                        dataRowId
                        globalKey
                    }
                    hasNextPage
                }
            }
        }
        """
        return query_str

    def get_data_row_ids(self, model_run_id: str) -> PaginatedCollection:
        """
        Fetches all data row ids that match this Slice

        Params
        model_run_id: str, required, uid or cuid of model run

        Returns:
            A PaginatedCollection of data row ids
        """
        return PaginatedCollection(
            client=self.client,
            query=ModelSlice.query_str(),
            params={"id": str(self.uid), "modelRunId": model_run_id},
            dereferencing=["getDataRowIdentifiersBySavedModelQuery", "nodes"],
            obj_class=lambda _, data_row_id_and_gk: data_row_id_and_gk.get(
                "id"
            ),
            cursor_path=[
                "getDataRowIdentifiersBySavedModelQuery",
                "pageInfo",
                "endCursor",
            ],
        )

    def get_data_row_identifiers(
        self, model_run_id: str
    ) -> PaginatedCollection:
        """
        Fetches all data row ids and global keys (where defined) that match this Slice

        Params:
        model_run_id : str, required, uid or cuid of model run

        Returns:
            A PaginatedCollection of Slice.DataRowIdAndGlobalKey
        """
        return PaginatedCollection(
            client=self.client,
            query=ModelSlice.query_str(),
            params={"id": str(self.uid), "modelRunId": model_run_id},
            dereferencing=["getDataRowIdentifiersBySavedModelQuery", "nodes"],
            obj_class=lambda _, data_row_id_and_gk: Slice.DataRowIdAndGlobalKey(
                data_row_id_and_gk.get("id"),
                data_row_id_and_gk.get("globalKey", None),
            ),
            cursor_path=[
                "getDataRowIdentifiersBySavedModelQuery",
                "pageInfo",
                "endCursor",
            ],
        )
