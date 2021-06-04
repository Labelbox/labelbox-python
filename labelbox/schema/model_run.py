from labelbox.orm.model import Field, Relationship
from labelbox.orm.db_object import DbObject


class ModelRun(DbObject):
    name = Field.String("name")
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    created_by_id = Field.String("created_by_id", "createdBy")

    def upsert_labels(self):
        ...

    def add_predictions(self, predictions):
        ...
