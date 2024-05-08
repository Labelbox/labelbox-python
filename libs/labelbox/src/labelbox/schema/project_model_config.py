from labelbox.orm.db_object import DbObject, Deletable
from labelbox.orm.model import Field, Relationship


class ProjectModelConfig(DbObject):
    """ A ProjectModelConfig represents an association between a project and a single model config.

    Attributes: 
        project_id (str): ID of project to associate
        model_config_id (str): ID of the model configuration
        model_config (ModelConfig): Configuration for model
    """

    project_id = Field.String("project_id", "projectId")
    model_config_id = Field.String("model_config_id", "modelConfigId")
    model_config = Relationship.ToOne("ModelConfig", False, "model_config")

    def delete(self) -> bool:
        """ Deletes this association between a model config and this project.

        Returns:
            bool, indicates if the operation was a success.
        """
        query = """mutation DeleteProjectModelConfigPyApi($id: ID!)  {
                    deleteProjectModelConfig(input: {id: $id}) {
                        success
                    }
                }"""

        params = {
            "id": self.uid,
        }
        result = self.client.execute(query, params)
        return result["deleteProjectModelConfig"]["success"]
