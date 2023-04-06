import logging
from typing import TYPE_CHECKING, Collection, Dict, List, Optional
import json
from labelbox.exceptions import ResourceNotFoundError

from labelbox.orm import query
from labelbox.orm.db_object import DbObject, Updateable, BulkDeletable
from labelbox.orm.model import Entity, Field, Relationship
from labelbox.schema.data_row_metadata import DataRowMetadataField  # type: ignore
from labelbox.schema.export_params import CatalogExportParams
from labelbox.schema.task import Task
from labelbox.schema.user import User  # type: ignore

if TYPE_CHECKING:
    from labelbox import AssetAttachment, Client

logger = logging.getLogger(__name__)


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
        Entity.AssetAttachment.AttachmentType.__members__)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attachments.supports_filtering = False
        self.attachments.supports_sorting = False

    def update(self, **kwargs):
        # Convert row data to string if it is an object
        # All other updates pass through
        row_data = kwargs.get("row_data")
        if isinstance(row_data, dict):
            kwargs['row_data'] = json.dumps(kwargs['row_data'])
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
                VIDEO, IMAGE, TEXT, IMAGE_OVERLAY (AssetAttachment.AttachmentType)
            attachment_value (str): Asset attachment value.
            attachment_name (str): (Optional) Asset attachment name.
        Returns:
            `AssetAttachment` DB object.
        Raises:
            ValueError: asset_type must be one of the supported types.
        """
        Entity.AssetAttachment.validate_attachment_type(attachment_type)

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
    def export_v2(client: 'Client',
                  data_rows: List['DataRow'],
                  task_name: Optional[str] = None,
                  params: Optional[CatalogExportParams] = None) -> Task:
        """
        Creates a data rows export task with the given list, params and returns the task.
        
        >>>     dataset = client.get_dataset(DATASET_ID)
        >>>     task = DataRow.export_v2(
        >>>         data_rows_ids=[data_row.uid for data_row in dataset.data_rows.list()],
        >>>         filters={
        >>>             "last_activity_at": ["2000-01-01 00:00:00", "2050-01-01 00:00:00"],
        >>>             "label_created_at": ["2000-01-01 00:00:00", "2050-01-01 00:00:00"]
        >>>         },
        >>>         params={
        >>>             "performance_details": False,
        >>>             "label_details": True
        >>>         })
        >>>     task.wait_till_done()
        >>>     task.result
        """
        print('export start')

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
        })

        mutation_name = "exportDataRowsInCatalog"
        create_task_query_str = """mutation exportDataRowsInCatalogPyApi($input: ExportDataRowsInCatalogInput!){
            %s(input: $input) {taskId} }
            """ % (mutation_name)

        data_rows_ids = [data_row.uid for data_row in data_rows]
        search_query: List[Dict[str, Collection[str]]] = []
        search_query.append({
            "ids": data_rows_ids,
            "operator": "is",
            "type": "data_row_id"
        })

        print(search_query)
        media_type_override = _params.get('media_type_override', None)

        if task_name is None:
            task_name = f"Export v2: data rows (%s)" % len(data_rows_ids)
        query_params = {
            "input": {
                "taskName": task_name,
                "filters": {
                    "searchQuery": {
                        "scope": None,
                        "query": search_query
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
                    "projectIds":
                        _params.get('project_ids', None),
                    "modelRunIds":
                        _params.get('model_run_ids', None),
                },
            }
        }

        res = client.execute(
            create_task_query_str,
            query_params,
        )
        print(res)
        res = res[mutation_name]
        task_id = res["taskId"]
        user: User = client.get_user()
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
