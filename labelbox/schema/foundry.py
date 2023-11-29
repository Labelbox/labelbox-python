from datetime import datetime
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel
from labelbox import exceptions
from labelbox.schema.identifiables import DataRowIds, GlobalKeys
from labelbox.schema.task import Task
from labelbox.utils import _CamelCaseMixin


class App(_CamelCaseMixin, BaseModel):
    id: Optional[str]
    model_id: str
    name: str
    description: str
    inference_params: Dict[str, Any]
    class_to_schema_id: Dict[str, str]
    created_by: Optional[str] = None

    @classmethod
    def type_name(cls):
        return "App"


class Model(_CamelCaseMixin, BaseModel):
    id: str
    description: str
    inference_params_json_schema: Dict
    name: str
    ontology_id: str
    created_at: datetime


APP_FIELD_NAMES = list(App.schema()['properties'].keys())
MODEL_FIELD_NAMES = list(Model.schema()['properties'].keys())


class FoundryClient:

    def __init__(self, client):
        self.client = client

    def _create_app(self, app: App) -> App:
        query_str = """
            mutation CreateDataRowAttachmentPyApi(
                $name: String!, $modelId: ID!, $description: String, $inferenceParams: Json!, $classToSchemaId: Json!
            ){
                createModelFoundryApp(input: {
                    name: $name 
                    modelId: $modelId 
                    description: $description
                    inferenceParams: $inferenceParams
                    classToSchemaId: $classToSchemaId
                })
                {
                    id
                    name
                    modelId
                    description
                    inferenceParams
                    classToSchemaId
                }
            }
            """

        params = app.dict(by_alias=True, exclude={"id"})

        response = self.client.execute(query_str, params)
        return App(**response["createModelFoundryApp"])

    def _get_app(self, id: str) -> App:
        field_names_str = "\n".join(APP_FIELD_NAMES)

        query_str = f"""
            query GetFoundryAppByIdPyApi($id: ID!) {{
                findModelFoundryApp(where: {{id: $id}}) {{
                    {field_names_str}
                }}
            }}
        """
        params = {"id": id}

        try:
            response = self.client.execute(query_str, params)
        except exceptions.InvalidQueryError as e:
            raise exceptions.ResourceNotFoundError(App, params)
        return App(**response["findModelFoundryApp"])

    def _delete_app(self, id: str) -> None:
        query_str = """
            mutation DeleteFoundryAppPyApi($id: ID!) {
                deleteModelFoundryApp(id: $id) {
                    success
                }
            }
        """
        params = {"id": id}
        self.client.execute(query_str, params)

    def _get_model(self, id: str) -> Model:
        field_names_str = "\n".join(MODEL_FIELD_NAMES)

        query_str = f"""
            query GetModelByIdPyApi($id: ID!) {{
                modelFoundryModel(where: {{id: $id}}) {{
                    model {{
                        {field_names_str}
                    }}
                }}
            }}
        """
        params = {"id": id}

        response = self.client.execute(query_str, params)
        return Model(**response["modelFoundryModel"]["model"])

    def run_app(self, model_run_name: str,
                data_rows: Union[DataRowIds, GlobalKeys], app_id: str) -> Task:
        app = self._get_app(app_id)
        model = self._get_model(app.model_id)

        if isinstance(data_rows, DataRowIds):
            data_rows_query = {
                "type": "data_row_id",
                "operator": "is",
                "ids": list(data_rows)
            }
        elif isinstance(data_rows, GlobalKeys):
            data_rows_query = {
                "type": "global_key",
                "operator": "is",
                "ids": list(data_rows)
            }
        else:
            raise ValueError(
                f"Invalid data_rows type {type(data_rows)}. Type of data_rows must be DataRowIds or GlobalKey"
            )

        params = {
            "modelId": str(app.model_id),
            "name": model_run_name,
            "classToSchemaId": app.class_to_schema_id,
            "inferenceParams": app.inference_params,
            "searchQuery": {
                "query": [data_rows_query],
                "scope": None
            },
            "ontologyId": model.ontology_id
        }

        query = """
        mutation CreateModelJobPyApi($input: CreateModelJobInput!) {
            createModelJob(input: $input) {
                taskId
                __typename
            }
        }
        """
        response = self.client.execute(query, {"input": params})
        task_id = response["createModelJob"]["taskId"]
        return Task.get_task(self.client, task_id)
