from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field, Relationship


class PredictionModel(DbObject):
    """ A prediction model represents a specific version of a model. """
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
    """ A prediction created by a PredictionModel. """
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    organization = Relationship.ToOne("Organization", False)

    label = Field.String("label")
    agreement = Field.Float("agreement")

    prediction_model = Relationship.ToOne("PredictionModel", False)
    data_row = Relationship.ToOne("DataRow", False)
    project = Relationship.ToOne("Project", False)
