import logging
from datetime import datetime
from typing import List, Dict, Union

from labelbox.orm import query
from labelbox.orm.db_object import DbObject, Updateable, BulkDeletable
from labelbox.orm.model import Entity, Field, Relationship
from labelbox.schema.asset_attachment import AssetAttachment

logger = logging.getLogger(__name__)


class DataRow(DbObject, Updateable, BulkDeletable):
    """ Internal Labelbox representation of a single piece of data (e.g. image, video, text).

    Attributes:
        external_id (str): User-generated file name or identifier
        row_data (str): Paths to local files are uploaded to Labelbox's server.
            Otherwise, it's treated as an external URL.
        updated_at (datetime)
        created_at (datetime)
        media_attributes (dict): generated media attributes for the datarow

        dataset (Relationship): `ToOne` relationship to Dataset
        created_by (Relationship): `ToOne` relationship to User
        organization (Relationship): `ToOne` relationship to Organization
        labels (Relationship): `ToMany` relationship to Label
        attachments (Relationship) `ToMany` relationship with AssetAttachment
    """
    external_id = Field.String("external_id")
    row_data = Field.String("row_data")
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    media_attributes = Field.Json("media_attributes")

    # Relationships
    dataset = Relationship.ToOne("Dataset")
    created_by = Relationship.ToOne("User", False, "created_by")
    organization = Relationship.ToOne("Organization", False)
    labels = Relationship.ToMany("Label", True)
    attachments = Relationship.ToMany("AssetAttachment", False, "attachments")

    supported_meta_types = supported_attachment_types = set(
        AssetAttachment.AttachmentType.__members__)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attachments.supports_filtering = False
        self.attachments.supports_sorting = False

    @staticmethod
    def bulk_delete(data_rows):
        """ Deletes all the given DataRows.

        Args:
            data_rows (list of DataRow): The DataRows to delete.
        """
        BulkDeletable._bulk_delete(data_rows, True)

    def create_attachment(self, attachment_type, attachment_value):
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
        AssetAttachment.validate_attachment_type(attachment_type)

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
