from labelbox.orm import query
from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Entity, Field, Relationship


class Model(DbObject):
    """A model represents a program that has been trained and
        can make predictions on new data.
        Attributes:
            name (str)
            model_runs (Relationship): `ToMany` relationship to ModelRun
        """

    name = Field.String("name")
    model_runs = Relationship.ToMany("ModelRun", False)

    def create_model_run(self, name):
        """ Creates a model run belonging to this model.

        Args:
            name (string): The name for the model run.
        Returns:
            ModelRun, the created model run.
        """
        name_param = "name"
        model_id_param = "modelId"
        ModelRun = Entity.ModelRun
        query_str = """mutation CreateModelRunPyApi($%s: String!, $%s: ID!) {
            createModelRun(data: {name: $%s, modelId: $%s}) {%s}}""" % (
            name_param, model_id_param, name_param, model_id_param,
            query.results_query_part(ModelRun))
        res = self.client.execute(query_str, {
            name_param: name,
            model_id_param: self.uid
        })
        return ModelRun(self.client, res["createModelRun"])
