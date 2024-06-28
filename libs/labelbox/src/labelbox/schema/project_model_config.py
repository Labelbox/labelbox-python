from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field, Relationship
from labelbox.exceptions import LabelboxError, error_message_for_unparsed_graphql_error


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

        try:
            result = self.client.execute(query, params)
        except LabelboxError as e:
            if e.message.startswith(
                    "Unknown error: "
            ):  # unfortunate hack to handle unparsed graphql errors
                error_content = error_message_for_unparsed_graphql_error(
                    e.message)
            else:
                error_content = e.message
            raise LabelboxError(message=error_content) from e

        return result["deleteProjectModelConfig"]["success"]
