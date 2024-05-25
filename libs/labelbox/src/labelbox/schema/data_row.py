import logging
from enum import Enum
from typing import TYPE_CHECKING, List, Optional, Tuple, Union, Any
import json

from labelbox.orm import query
from labelbox.orm.db_object import DbObject, Updateable, BulkDeletable, experimental
from labelbox.orm.model import Entity, Field, Relationship
from labelbox.schema.asset_attachment import AttachmentType
from labelbox.schema.data_row_metadata import DataRowMetadataField  # type: ignore
from labelbox.schema.export_filters import DatarowExportFilters, build_filters, validate_at_least_one_of_data_row_ids_or_global_keys
from labelbox.schema.export_params import CatalogExportParams, validate_catalog_export_params
from labelbox.schema.export_task import ExportTask
from labelbox.schema.task import Task

if TYPE_CHECKING:
    from labelbox import AssetAttachment, Client

logger = logging.getLogger(__name__)


class KeyType(str, Enum):
    ID = 'ID'
    """An existing CUID"""
    GKEY = 'GKEY'
    """A Global key, could be existing or non-existing"""
    AUTO = 'AUTO'
    """The key will be auto-generated. Only usable for creates"""


class DataRow(DbObject, Updateable, BulkDeletable):
    """ Internal Labelbox representation of a single piece of data (e.g. image, video, text).

    Attributes:
        external_id (str): User-generated file name or identifier
        global_key (str): User-generated globally unique identifier
        row_data (str): Paths to local files are uploaded to Labelbox's server.
            Otherwise, it's treated as an external URL.
        updated_at (datetime)
        created_at (datetime)
        media_attributes (dict): generated media attributes for the data row
        metadata_fields (list): metadata associated with the data row
        metadata (list): metadata associated with the data row as list of DataRowMetadataField.
            When importing Data Rows with metadata, use `metadata_fields` instead

        dataset (Relationship): `ToOne` relationship to Dataset
        created_by (Relationship): `ToOne` relationship to User
        organization (Relationship): `ToOne` relationship to Organization
        labels (Relationship): `ToMany` relationship to Label
        attachments (Relationship) `ToMany` relationship with AssetAttachment
    """
    external_id = Field.String("external_id")
    global_key = Field.String("global_key")
    row_data = Field.String("row_data")
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    media_attributes = Field.Json("media_attributes")
    metadata_fields = Field.List(
        dict,
        graphql_type="DataRowCustomMetadataUpsertInput!",
        name="metadata_fields",
        result_subquery="metadataFields { schemaId name value kind }")
    metadata = Field.List(DataRowMetadataField,
                          name="metadata",
                          graphql_name="customMetadata",
                          result_subquery="customMetadata { schemaId value }")

    # Relationships
    dataset = Relationship.ToOne("Dataset")
    created_by = Relationship.ToOne("User", False, "created_by")
    organization = Relationship.ToOne("Organization", False)
    labels = Relationship.ToMany("Label", True)
    attachments = Relationship.ToMany("AssetAttachment", False, "attachments")

    supported_meta_types = supported_attachment_types = set(
        AttachmentType.__members__)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attachments.supports_filtering = False
        self.attachments.supports_sorting = False

    def update(self, **kwargs):
        # Convert row data to string if it is an object
        # All other updates pass through
        primary_fields = ["external_id", "global_key", "row_data"]
        for field in primary_fields:
            data = kwargs.get(field)
            if data == "" or data == {}:
                raise ValueError(f"{field} cannot be empty if it is set")
        if not any(kwargs.get(field) for field in primary_fields):
            raise ValueError(
                f"At least one of these fields needs to be present: {primary_fields}"
            )

        row_data = kwargs.get("row_data")
        if isinstance(row_data, dict):
            kwargs['row_data'] = json.dumps(row_data)
        super().update(**kwargs)

    @staticmethod
    def bulk_delete(data_rows) -> None:
        """ Deletes all the given DataRows.

        Args:
            data_rows (list of DataRow): The DataRows to delete.
        """
        BulkDeletable._bulk_delete(data_rows, True)

    def get_winning_label_id(self, project_id: str) -> Optional[str]:
        """ Retrieves the winning label ID, i.e. the one that was marked as the
            best for a particular data row, in a project's workflow.

        Args:
            project_id (str): ID of the project containing the data row
        """
        data_row_id_param = "dataRowId"
        project_id_param = "projectId"
        query_str = """query GetWinningLabelIdPyApi($%s: ID!, $%s: ID!) {
            dataRow(where: { id: $%s }) {
                labelingActivity(where: { projectId: $%s }) {
                    selectedLabelId
                }
            }} """ % (data_row_id_param, project_id_param, data_row_id_param,
                      project_id_param)

        res = self.client.execute(query_str, {
            data_row_id_param: self.uid,
            project_id_param: project_id,
        })

        return res["dataRow"]["labelingActivity"]["selectedLabelId"]

    def create_attachment(self,
                          attachment_type,
                          attachment_value,
                          attachment_name=None) -> "AssetAttachment":
        """ Adds an AssetAttachment to a DataRow.
            Labelers can view these attachments while labeling.

            >>> datarow.create_attachment("TEXT", "This is a text message")

        Args:
            attachment_type (str): Asset attachment type, must be one of:
                VIDEO, IMAGE, TEXT, IMAGE_OVERLAY (AttachmentType)
            attachment_value (str): Asset attachment value.
            attachment_name (str): (Optional) Asset attachment name.
        Returns:
            `AssetAttachment` DB object.
        Raises:
            ValueError: attachment_type must be one of the supported types.
            ValueError: attachment_value must be a non-empty string.
        """
        Entity.AssetAttachment.validate_attachment_json({
            'type': attachment_type,
            'value': attachment_value
        })

        attachment_type_param = "type"
        attachment_value_param = "value"
        attachment_name_param = "name"
        data_row_id_param = "dataRowId"

        query_str = """mutation CreateDataRowAttachmentPyApi(
            $%s: AttachmentType!, $%s: String!, $%s: String, $%s: ID!) {
            createDataRowAttachment(data: {
                type: $%s value: $%s name: $%s dataRowId: $%s}) {%s}} """ % (
            attachment_type_param, attachment_value_param,
            attachment_name_param, data_row_id_param, attachment_type_param,
            attachment_value_param, attachment_name_param, data_row_id_param,
            query.results_query_part(Entity.AssetAttachment))

        res = self.client.execute(
            query_str, {
                attachment_type_param: attachment_type,
                attachment_value_param: attachment_value,
                attachment_name_param: attachment_name,
                data_row_id_param: self.uid
            })
        return Entity.AssetAttachment(self.client,
                                      res["createDataRowAttachment"])

    @staticmethod
    def export(
        client: "Client",
        data_rows: Optional[List[Union[str, "DataRow"]]] = None,
        global_keys: Optional[List[str]] = None,
        task_name: Optional[str] = None,
        params: Optional[CatalogExportParams] = None,
    ) -> ExportTask:
        """
        Creates a data rows export task with the given list, params and returns the task.
        Args:
            client (Client): client to use to make the export request
            data_rows (list of DataRow or str): list of data row objects or data row ids to export
            task_name (str): name of remote task
            params (CatalogExportParams): export params

        >>>     dataset = client.get_dataset(DATASET_ID)
        >>>     task = DataRow.export(
        >>>         data_rows=[data_row.uid for data_row in dataset.data_rows.list()],
        >>>             # or a list of DataRow objects: data_rows = data_set.data_rows.list()
        >>>             # or a list of global_keys=["global_key_1", "global_key_2"],
        >>>             # Note that exactly one of: data_rows or global_keys parameters can be passed in at a time
        >>>             # and if data rows ids is present, global keys will be ignored
        >>>         params={
        >>>             "performance_details": False,
        >>>             "label_details": True
        >>>         })
        >>>     task.wait_till_done()
        >>>     task.result
        """
        task, _ = DataRow._export(client,
                                  data_rows,
                                  global_keys,
                                  task_name,
                                  params,
                                  streamable=True)
        return ExportTask(task)

    @staticmethod
    def export_v2(
        client: "Client",
        data_rows: Optional[List[Union[str, "DataRow"]]] = None,
        global_keys: Optional[List[str]] = None,
        task_name: Optional[str] = None,
        params: Optional[CatalogExportParams] = None,
    ) -> Union[Task, ExportTask]:
        """
        Creates a data rows export task with the given list, params and returns the task.
        Args:
            client (Client): client to use to make the export request
            data_rows (list of DataRow or str): list of data row objects or data row ids to export
            task_name (str): name of remote task
            params (CatalogExportParams): export params


        >>>     dataset = client.get_dataset(DATASET_ID)
        >>>     task = DataRow.export_v2(
        >>>         data_rows=[data_row.uid for data_row in dataset.data_rows.list()],
        >>>             # or a list of DataRow objects: data_rows = data_set.data_rows.list()
        >>>             # or a list of global_keys=["global_key_1", "global_key_2"],
        >>>             # Note that exactly one of: data_rows or global_keys parameters can be passed in at a time
        >>>             # and if data rows ids is present, global keys will be ignored
        >>>         params={
        >>>             "performance_details": False,
        >>>             "label_details": True
        >>>         })
        >>>     task.wait_till_done()
        >>>     task.result
        """
        task, is_streamable = DataRow._export(client, data_rows, global_keys,
                                              task_name, params)
        if is_streamable:
            return ExportTask(task, True)
        return task

    @staticmethod
    def _export(
        client: "Client",
        data_rows: Optional[List[Union[str, "DataRow"]]] = None,
        global_keys: Optional[List[str]] = None,
        task_name: Optional[str] = None,
        params: Optional[CatalogExportParams] = None,
        streamable: bool = False,
    ) -> Tuple[Task, bool]:
        _params = params or CatalogExportParams({
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
        })

        validate_catalog_export_params(_params)

        mutation_name = "exportDataRowsInCatalog"
        create_task_query_str = (
            f"mutation {mutation_name}PyApi"
            f"($input: ExportDataRowsInCatalogInput!)"
            f"{{{mutation_name}(input: $input){{taskId isStreamable}}}}")

        data_row_ids = []
        if data_rows is not None:
            for dr in data_rows:
                if isinstance(dr, DataRow):
                    data_row_ids.append(dr.uid)
                elif isinstance(dr, str):
                    data_row_ids.append(dr)

        filters = DatarowExportFilters({
            "data_row_ids": data_row_ids,
            "global_keys": None,
        }) if data_row_ids else DatarowExportFilters({
            "data_row_ids": None,
            "global_keys": global_keys,
        })
        validate_at_least_one_of_data_row_ids_or_global_keys(filters)

        search_query = build_filters(client, filters)
        media_type_override = _params.get('media_type_override', None)

        if task_name is None:
            task_name = f"Export v2: data rows {len(data_row_ids)}"
        query_params = {
            "input": {
                "taskName": task_name,
                "filters": {
                    "searchQuery": {
                        "scope": None,
                        "query": search_query
                    }
                },
                "isStreamableReady": True,
                "params": {
                    "mediaTypeOverride":
                        media_type_override.value
                        if media_type_override is not None else None,
                    "includeAttachments":
                        _params.get('attachments', False),
                    "includeEmbeddings":
                        _params.get('embeddings', False),
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
                "streamable": streamable
            }
        }

        res = client.execute(create_task_query_str,
                             query_params,
                             error_log_key="errors")
        res = res[mutation_name]
        task_id = res["taskId"]
        is_streamable = res["isStreamable"]
        return Task.get_task(client, task_id), is_streamable
