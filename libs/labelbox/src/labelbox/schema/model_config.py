from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field


class ModelConfig(DbObject):
    """A ModelConfig represents a set of inference params configured for a model

    Attributes:
        inference_params (JSON): Dict of inference params
        model_id (str): ID of the model to configure
        name (str): Name of config
    """

    inference_params = Field.Json("inference_params", "inferenceParams")
    model_id = Field.String("model_id", "modelId")
    name = Field.String("name", "name")
