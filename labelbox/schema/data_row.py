from labelbox.orm import query
from labelbox.orm.db_object import DbObject, Updateable, BulkDeletable
from labelbox.orm.model import Entity, Field, Relationship
from labelbox.schema.asset_metadata import AssetMetadata


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
        metadata (Relationship): `ToMany` relationship to AssetMetadata
        predictions (Relationship): `ToMany` relationship to Prediction
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
    metadata = Relationship.ToMany("AssetMetadata", False, "metadata")

    predictions = Relationship.ToMany("Prediction", False)

    supported_meta_types = {
        meta_type.value for meta_type in AssetMetadata.MetaType
    }

    @staticmethod
    def bulk_delete(data_rows):
        """ Deletes all the given DataRows.

        Args:
            data_rows (list of DataRow): The DataRows to delete.
        """
        BulkDeletable._bulk_delete(data_rows, True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metadata.supports_filtering = False
        self.metadata.supports_sorting = False

    def create_metadata(self, meta_type, meta_value):
        """ Attaches asset metadata to a DataRow.

            >>> datarow.create_metadata("TEXT", "This is a text message")

        Args:
            meta_type (str): Asset metadata type, must be one of:
                VIDEO, IMAGE, TEXT, IMAGE_OVERLAY (AssetMetadata.MetaType)
            meta_value (str): Asset metadata value.
        Returns:
            `AssetMetadata` DB object.
        Raises:
            ValueError: meta_type must be one of the supported types.
        """

        if meta_type not in self.supported_meta_types:
            raise ValueError(
                f"meta_type must be one of {self.supported_meta_types}. Found {meta_type}"
            )

        meta_type_param = "metaType"
        meta_value_param = "metaValue"
        data_row_id_param = "dataRowId"
        query_str = """mutation CreateAssetMetadataPyApi(
            $%s: AttachmentType!, $%s: String!, $%s: ID!) {
            createAssetMetadata(data: {
                metaType: $%s metaValue: $%s dataRowId: $%s}) {%s}} """ % (
            meta_type_param, meta_value_param, data_row_id_param,
            meta_type_param, meta_value_param, data_row_id_param,
            query.results_query_part(Entity.AssetMetadata))

        res = self.client.execute(
            query_str, {
                meta_type_param: meta_type,
                meta_value_param: meta_value,
                data_row_id_param: self.uid
            })
        return Entity.AssetMetadata(self.client, res["createAssetMetadata"])
