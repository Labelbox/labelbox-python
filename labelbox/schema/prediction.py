from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field, Relationship


class PredictionModel(DbObject):
    """ A PredictionModel creates a Prediction. Legacy editor only.

    Refer to BulkImportRequest if using the new Editor.

    Attributes:
        updated_at (datetime)
        created_at (datetime)
        name (str)
        slug (str)
        version (int)

        created_by (Relationship): `ToOne` relationship to User
        organization (Relationship): `ToOne` relationship to Organization
    """
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    created_by = Relationship.ToOne("User", False, "created_by")
    organization = Relationship.ToOne("Organization", False)

    name = Field.String("name")
    slug = Field.String("slug")
    version = Field.Int("version")

    created_predictions = Relationship.ToMany("Prediction", False,
                                              "created_predictions")


class Prediction(DbObject):
    """ A prediction created by a PredictionModel. Legacy editor only.

    Refer to BulkImportRequest if using the new Editor.

    Attributes:
        updated_at (datetime)
        created_at (datetime)
        label (str)
        agreement (float)

        organization (Relationship): `ToOne` relationship to Organization
        prediction_model (Relationship): `ToOne` relationship to PredictionModel
        data_row (Relationship): `ToOne` relationship to DataRow
        project (Relationship): `ToOne` relationship to Project
    """
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    organization = Relationship.ToOne("Organization", False)

    label = Field.String("label")
    agreement = Field.Float("agreement")

    prediction_model = Relationship.ToOne("PredictionModel", False)
    data_row = Relationship.ToOne("DataRow", False)
    project = Relationship.ToOne("Project", False)
