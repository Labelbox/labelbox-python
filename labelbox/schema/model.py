from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field, Relationship


class Model(DbObject):
        """A model represents a program that has been trained and
        can make predictions on new data.
        Attributes:
            name (str)
            ontology (Relationship): `ToOne` relationship to Ontology
            model_runs (Relationship): `ToMany` relationship to ModelRun (TODO)
            slices (Relationship): `ToMany` relationship to Slice (TODO)
        """

        name = Field.String("name")
        ontology_id = Field.String("Ontology", "ontology_id")

        model_runs = Relationship.ToMany("ModelRun", False)
