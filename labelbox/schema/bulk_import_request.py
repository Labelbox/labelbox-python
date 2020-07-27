import json
from pathlib import Path
from typing import BinaryIO
from typing import Iterable
from typing import Tuple
from typing import Union

import ndjson
import requests

import labelbox.exceptions
from labelbox import Client
from labelbox.orm import query
from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field
from labelbox.orm.model import Relationship
from labelbox.schema.enums import BulkImportRequestState

NDJSON_MIME_TYPE = "application/x-ndjson"


class BulkImportRequest(DbObject):
    project = Relationship.ToOne("Project", False)
    name = Field.String("name")
    created_at = Field.DateTime("created_at")
    created_by = Relationship.ToOne("User", False, "created_by")
    input_file_url = Field.String("input_file_url")
    error_file_url = Field.String("error_file_url")
    status_file_url = Field.String("status_file_url")
    state = Field.Enum(BulkImportRequestState, "state")

    @classmethod
    def create_from_url(
            cls, client: Client, project_id: str, name: str,
            url: str) -> 'BulkImportRequest':
        query_str = """
        mutation {
            createBulkImportRequest(data: {
                projectId: "%s",
                name: "%s",
                fileUrl: "%s"
            }) {
                %s
            }
        }
        """ % (
            project_id,
            name,
            url,
            query.results_query_part(BulkImportRequest)
        )
        bulk_import_request_kwargs = client.execute(query_str)["createBulkImportRequest"]
        return BulkImportRequest(client, bulk_import_request_kwargs)

    @classmethod
    def create_from_objects(
            cls, client: Client, project_id: str, name: str,
            predictions: Iterable[dict]) -> 'BulkImportRequest':
        data_str = ndjson.dumps(predictions)
        data = data_str.encode('utf-8')
        file_name = cls.__make_file_name(project_id, name)
        request_data = cls.__make_request_data(project_id, name, len(data_str), file_name)
        file_data = (file_name, data, NDJSON_MIME_TYPE)
        response_data = cls.__send_create_file_command(
            client, request_data, file_name, file_data)
        return BulkImportRequest(client, response_data["createBulkImportRequest"])

    @classmethod
    def create_from_local_file(
            cls, client: Client, project_id: str, name: str,
            file: Path, validate_file=True) -> 'BulkImportRequest':
        file_name = cls.__make_file_name(project_id, name)
        content_length = file.stat().st_size
        request_data = cls.__make_request_data(project_id, name, content_length, file_name)
        with file.open('rb') as f:
            if validate_file:
                data = f.read()
                try:
                    ndjson.loads(data)
                except ValueError:
                    raise ValueError(f"{file} is not a valid ndjson file")
                file_data = (file.name, data, NDJSON_MIME_TYPE)
            else:
                file_data = (file.name, f, NDJSON_MIME_TYPE)
            response_data = cls.__send_create_file_command(
                client, request_data, file_name, file_data)
        return BulkImportRequest(client, response_data["createBulkImportRequest"])

    @classmethod
    def __make_file_name(cls, project_id: str, name: str) -> str:
        return f"{project_id}__{name}.ndjson"

    # TODO(gszpak): move it to client.py
    @classmethod
    def __make_request_data(
            cls, project_id: str, name: str,
            content_length: int, file_name: str) -> dict:
        query_str = """
        mutation createBulkImportRequestFromFile($projectId: ID!,
                $name: String!, $file: Upload!, $contentLength: Int!) {
            createBulkImportRequest(data: {
                projectId: $projectId,
                name: $name,
                filePayload: {
                    file: $file,
                    contentLength: $contentLength
                }
            }) {
                %s
            }
        }
        """ % (query.results_query_part(BulkImportRequest))
        variables = {
            "projectId": project_id,
            "name": name,
            "file": None,
            "contentLength": content_length
        }
        operations = json.dumps({
            "variables": variables,
            "query": query_str
        })

        return {
            "operations": operations,
            "map": (
                None,
                json.dumps({
                    file_name: ["variables.file"]
                })
            )
        }

    # TODO(gszpak): move it to client.py
    @classmethod
    def __send_create_file_command(
            cls, client: Client, request_data: dict,
            file_name: str, file_data: Tuple[str, Union[bytes, BinaryIO], str]) -> dict:
        response = requests.post(
            client.endpoint,
            headers={
                "authorization": "Bearer %s" % client.api_key
            },
            data=request_data,
            files={
                file_name: file_data
            }
        )

        try:
            response_json = response.json()
        except ValueError:
            raise labelbox.exceptions.LabelboxError(
                "Failed to parse response as JSON: %s" % response.text)

        response_data = response_json.get("data", None)
        if response_data is None:
            raise labelbox.exceptions.LabelboxError(
                "Failed to upload, message: %s" % response_json.get("errors", None))

        if not response_data.get("createBulkImportRequest", None):
            raise labelbox.exceptions.LabelboxError(
                "Failed to create BulkImportRequest, message: %s" %
                response_json.get("errors", None) or response_data.get("error", None))

        return response_data
