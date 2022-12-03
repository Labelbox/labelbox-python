import logging
from typing import TYPE_CHECKING, Optional
import json

from labelbox.orm import query
from labelbox.orm.db_object import DbObject, Updateable, BulkDeletable
from labelbox.orm.model import Entity, Field, Relationship
from labelbox.schema.data_row_metadata import DataRowMetadataField  # type: ignore

if TYPE_CHECKING:
    from labelbox import AssetAttachment

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

    def create_attachment(self, attachment_type,
                          attachment_value) -> "AssetAttachment":
        """ Adds an AssetAttachment to a DataRow.
            Labelers can view these attachments while labeling.

            >>> datarow.create_attachment("TEXT", "This is a text message")

        Args:
            attachment_type (str): Asset attachment type, must be one of:
                VIDEO, IMAGE, TEXT, IMAGE_OVERLAY (AssetAttachment.AttachmentType)
            attachment_value (str): Asset attachment value.
        Returns:
            `AssetAttachment` DB object.
        Raises:
            ValueError: asset_type must be one of the supported types.
        """
        Entity.AssetAttachment.validate_attachment_type(attachment_type)

        attachment_type_param = "type"
        attachment_value_param = "value"
        data_row_id_param = "dataRowId"
        query_str = """mutation CreateDataRowAttachmentPyApi(
            $%s: AttachmentType!, $%s: String!, $%s: ID!) {
            createDataRowAttachment(data: {
                type: $%s value: $%s dataRowId: $%s}) {%s}} """ % (
            attachment_type_param, attachment_value_param, data_row_id_param,
            attachment_type_param, attachment_value_param, data_row_id_param,
            query.results_query_part(Entity.AssetAttachment))

        res = self.client.execute(
            query_str, {
                attachment_type_param: attachment_type,
                attachment_value_param: attachment_value,
                data_row_id_param: self.uid
            })
        return Entity.AssetAttachment(self.client,
                                      res["createDataRowAttachment"])
