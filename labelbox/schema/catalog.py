from typing import Any, Dict, List, Optional, Union
from labelbox.orm.db_object import experimental
from labelbox.schema.export_filters import CatalogExportFilters, build_filters

from labelbox.schema.export_params import (CatalogExportParams,
                                           validate_catalog_export_params)
from labelbox.schema.export_task import ExportTask
from labelbox.schema.task import Task

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from labelbox import Client


class Catalog:
    client: "Client"

    def __init__(self, client: 'Client'):
        self.client = client

    def export_v2(
        self,
        task_name: Optional[str] = None,
        filters: Union[CatalogExportFilters, Dict[str, List[str]], None] = None,
        params: Optional[CatalogExportParams] = None,
    ) -> Task:
        """
        Creates a catalog export task with the given params, filters and returns the task.
        
        >>>     import labelbox as lb
        >>>     client = lb.Client(<API_KEY>)
        >>>     catalog = client.get_catalog()
        >>>     task = catalog.export_v2(
        >>>         filters={
        >>>             "last_activity_at": ["2000-01-01 00:00:00", "2050-01-01 00:00:00"],
        >>>             "label_created_at": ["2000-01-01 00:00:00", "2050-01-01 00:00:00"],
        >>>         },
        >>>         params={
        >>>             "performance_details": False,
        >>>             "label_details": True
        >>>         })
        >>>     task.wait_till_done()
        >>>     task.result
        """
        return self._export(task_name, filters, params, False)

    @experimental
    def export(
        self,
        task_name: Optional[str] = None,
        filters: Union[CatalogExportFilters, Dict[str, List[str]], None] = None,
        params: Optional[CatalogExportParams] = None,
    ) -> ExportTask:
        """
        Creates a catalog export task with the given params, filters and returns the task.

        >>>     import labelbox as lb
        >>>     client = lb.Client(<API_KEY>)
        >>>     export_task = Catalog.export(
        >>>         filters={
        >>>             "last_activity_at": ["2000-01-01 00:00:00", "2050-01-01 00:00:00"],
        >>>             "label_created_at": ["2000-01-01 00:00:00", "2050-01-01 00:00:00"],
        >>>         },
        >>>         params={
        >>>             "performance_details": False,
        >>>             "label_details": True
        >>>         })
        >>>     export_task.wait_till_done()
        >>>
        >>>     # Return a JSON output string from the export task results/errors one by one:
        >>>     def json_stream_handler(output: lb.JsonConverterOutput):
        >>>       print(output.json_str)
        >>>
        >>>     if export_task.has_errors():
        >>>       export_task.get_stream(
        >>>         converter=lb.JsonConverter(),
        >>>         stream_type=lb.StreamType.ERRORS
        >>>       ).start(stream_handler=lambda error: print(error))
        >>>
        >>>     if export_task.has_result():
        >>>       export_json = export_task.get_stream(
        >>>         converter=lb.JsonConverter(),
        >>>         stream_type=lb.StreamType.RESULT
        >>>       ).start(stream_handler=json_stream_handler)
        """
        task = self._export(task_name, filters, params, True)
        return ExportTask(task)

    def _export(self,
                task_name: Optional[str] = None,
                filters: Union[CatalogExportFilters, Dict[str, List[str]],
                               None] = None,
                params: Optional[CatalogExportParams] = None,
                streamable: bool = False) -> Task:

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
            "all_projects": False,
            "all_model_runs": False,
        })
        validate_catalog_export_params(_params)

        _filters = filters or CatalogExportFilters({
            "last_activity_at": None,
            "label_created_at": None,
            "data_row_ids": None,
            "global_keys": None,
        })

        mutation_name = "exportDataRowsInCatalog"
        create_task_query_str = (
            f"mutation {mutation_name}PyApi"
            f"($input: ExportDataRowsInCatalogInput!)"
            f"{{{mutation_name}(input: $input){{taskId}}}}")

        media_type_override = _params.get('media_type_override', None)
        query_params: Dict[str, Any] = {
            "input": {
                "taskName": task_name,
                "filters": {
                    "searchQuery": {
                        "scope": None,
                        "query": None,
                    }
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
                    "allProjects":
                        _params.get('all_projects', False),
                    "allModelRuns":
                        _params.get('all_model_runs', False),
                },
                "streamable": streamable,
            }
        }

        search_query = build_filters(self.client, _filters)
        query_params["input"]["filters"]["searchQuery"]["query"] = search_query

        res = self.client.execute(create_task_query_str,
                                  query_params,
                                  error_log_key="errors")
        res = res[mutation_name]
        task_id = res["taskId"]
        return Task.get_task(self.client, task_id)
