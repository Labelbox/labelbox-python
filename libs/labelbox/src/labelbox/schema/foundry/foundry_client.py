from typing import Union
from labelbox import exceptions
from labelbox.schema.foundry.app import App, APP_FIELD_NAMES
from labelbox.schema.identifiables import DataRowIds, GlobalKeys, IdType
from labelbox.schema.task import Task


class FoundryClient:
    def __init__(self, client):
        self.client = client

    def _create_app(self, app: App) -> App:
        field_names_str = "\n".join(APP_FIELD_NAMES)
        query_str = f"""
            mutation CreateFoundryAppPyApi(
                $name: String!, $modelId: ID!, $ontologyId: ID!, $description: String, $inferenceParams: Json!, $classToSchemaId: Json!
            ){{
                createModelFoundryApp(input: {{
                    name: $name 
                    modelId: $modelId 
                    ontologyId: $ontologyId
                    description: $description
                    inferenceParams: $inferenceParams
                    classToSchemaId: $classToSchemaId
                }})
                {{
                    {field_names_str}
                }}
            }}
            """

        params = app.model_dump(by_alias=True, exclude={"id"})

        try:
            response = self.client.execute(query_str, params)
        except exceptions.LabelboxError as e:
            raise exceptions.LabelboxError("Unable to create app", e)
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
        except Exception as e:
            raise exceptions.LabelboxError(f"Unable to get app with id {id}", e)
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
        try:
            self.client.execute(query_str, params)
        except Exception as e:
            raise exceptions.LabelboxError(
                f"Unable to delete app with id {id}", e
            )

    def run_app(
        self,
        model_run_name: str,
        data_rows: Union[DataRowIds, GlobalKeys],
        app_id: str,
    ) -> Task:
        app = self._get_app(app_id)

        params = {
            "modelId": str(app.model_id),
            "name": model_run_name,
            "classToSchemaId": app.class_to_schema_id,
            "inferenceParams": app.inference_params,
            "ontologyId": app.ontology_id,
        }

        data_rows_key = (
            "dataRowIds"
            if data_rows.id_type == IdType.DataRowId
            else "globalKeys"
        )
        params[data_rows_key] = list(data_rows)

        query = """
        mutation CreateModelJobPyApi($input: CreateModelJobForDataRowsInput!) {
            createModelJobForDataRows(input: $input) {
                taskId
                __typename
            }
        }
        """
        try:
            response = self.client.execute(query, {"input": params})
        except Exception as e:
            raise exceptions.LabelboxError("Unable to run foundry app", e)
        task_id = response["createModelJobForDataRows"]["taskId"]
        return Task.get_task(self.client, task_id)
