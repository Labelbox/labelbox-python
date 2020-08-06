import json
import logging
import time
from pathlib import Path
from typing import BinaryIO
from typing import Iterable
from typing import Tuple
from typing import Union

import backoff
import ndjson
import requests

import labelbox.exceptions
from labelbox import Project
from labelbox import User
from labelbox.orm import query
from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field
from labelbox.orm.model import Relationship
from labelbox.schema.enums import BulkImportRequestState

NDJSON_MIME_TYPE = "application/x-ndjson"
logger = logging.getLogger(__name__)


def __make_file_name(project_id: str, name: str) -> str:
    return f"{project_id}__{name}.ndjson"


# TODO(gszpak): all the code below should be handled automatically by Relationship
def __build_results_query_part() -> str:
    return """
        project {
            %s
        }
        createdBy {
            %s
        }
        %s
    """ % (
        query.results_query_part(Project),
        query.results_query_part(User),
        query.results_query_part(BulkImportRequest))


class BulkImportRequest(DbObject):
    project = Relationship.ToOne("Project")
    name = Field.String("name")
    created_at = Field.DateTime("created_at")
    created_by = Relationship.ToOne("User", False, "created_by")
    input_file_url = Field.String("input_file_url")
    error_file_url = Field.String("error_file_url")
    status_file_url = Field.String("status_file_url")
    state = Field.Enum(BulkImportRequestState, "state")

    # TODO(gszpak): building query body should be handled by the client
    def get(self, project_id: str, name: str) -> 'BulkImportRequest':
        """
        Fetches existing BulkImportRequest.

        Args:
            client (Client): a Labelbox client
            project_id (str): BulkImportRequest's project id
            name (str): name of BulkImportRequest
        Returns:
            BulkImportRequest object
        """
        query_str = """query getBulkImportRequestPyApi(
                $projectId: ID!, $name: String!) {
            bulkImportRequest(where: {
                projectId: $projectId,
                name: $name
            }) {
                %s
            }
        }
        """ % __build_results_query_part()
        params = {"projectId": project_id, "name": name}
        bulk_import_request_kwargs = self.client.execute(
            query_str, params=params).get("bulkImportRequest")
        if bulk_import_request_kwargs is None:
            raise labelbox.exceptions.ResourceNotFoundError(
                BulkImportRequest, {
                    "projectId": project_id,
                    "name": name
                })
        return BulkImportRequest.from_result(self.client, bulk_import_request_kwargs)

    def refresh(self) -> None:
        """
        Synchronizes values of all fields with the database.
        """
        bulk_import_request = self.get(self.client,
                                       self.project().uid, self.name)
        for field in self.fields():
            setattr(self, field.name, getattr(bulk_import_request, field.name))

    def wait_until_done(self, sleep_time_seconds: int = 30) -> None:
        """
        Blocks until the BulkImportRequest.state changes either to
        `BulkImportRequestState.FINISHED` or `BulkImportRequestState.FAILED`,
        periodically refreshing object's state.

        Args:
            sleep_time_seconds (str): a time to block between subsequent API calls
        """
        while self.state == BulkImportRequestState.RUNNING:
            logger.info(f"Sleeping for {sleep_time_seconds} seconds...")
            time.sleep(sleep_time_seconds)
            self.__exponential_backoff_refresh()

    @backoff.on_exception(
        backoff.expo,
        (labelbox.exceptions.ApiLimitError, labelbox.exceptions.TimeoutError,
         labelbox.exceptions.NetworkError),
        max_tries=10,
        jitter=None)
    def __exponential_backoff_refresh(self) -> None:
        self.refresh()

    # TODO(gszpak): project() and created_by() methods
    # TODO(gszpak): are hacky ways to eagerly load the relationships
    def project(self):  # type: ignore
        if self.__project is not None:
            return self.__project
        return None

    def created_by(self):  # type: ignore
        if self.__user is not None:
            return self.__user
        return None

    # TODO(gszpak): move it to client.py
    def __make_request_data(self, name: str, content_length: int,
                            file_name: str) -> dict:
        query_str = """mutation createBulkImportRequestFromFilePyApi(
                $projectId: ID!, $name: String!, $file: Upload!, $contentLength: Int!) {
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
        """ % __build_results_query_part()
        variables = {
            "projectId": self.project.uid,
            "name": name,
            "file": None,
            "contentLength": content_length
        }
        operations = json.dumps({"variables": variables, "query": query_str})

        return {
            "operations": operations,
            "map": (None, json.dumps({file_name: ["variables.file"]}))
        }

    # TODO(gszpak): move it to client.py
    def __send_create_file_command(
            self, request_data: dict, file_name: str,
            file_data: Tuple[str, Union[bytes, BinaryIO], str]) -> dict:
        response = requests.post(
            self.client.endpoint,
            headers={"authorization": "Bearer %s" % self.client.api_key},
            data=request_data,
            files={file_name: file_data})

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
                response_json.get("errors", None) or
                response_data.get("error", None))

        return response_data

    def from_result(result: dict) -> 'BulkImportRequest':
        project = result.pop("project")
        user = result.pop("createdBy")
        bulk_import_request = BulkImportRequest(self.client, result)
        if project is not None:
            bulk_import_request.__project = Project(  # type: ignore
                self.client, project)
        if user is not None:
            bulk_import_request.__user = User(self.client, user)  # type: ignore
        return bulk_import_request


def create_from_url(client, project_id: str, name: str,
                    url: str) -> BulkImportRequest:
    """
    Creates a BulkImportRequest from a publicly accessible URL
    to an ndjson file with predictions.

    Args:
        client (Client): a Labelbox client
        project_id (str): id of project for which predictions will be imported
        name (str): name of BulkImportRequest
        url (str): publicly accessible URL pointing to ndjson file containing predictions
    Returns:
        BulkImportRequest object
    """
    query_str = """mutation createBulkImportRequestPyApi(
            $projectId: ID!, $name: String!, $fileUrl: String!) {
        createBulkImportRequest(data: {
            projectId: $projectId,
            name: $name,
            fileUrl: $fileUrl
        }) {
            %s
        }
    }
    """ % __build_results_query_part()
    params = {"projectId": project_id, "name": name, "fileUrl": url}
    bulk_import_request_response = client.execute(query_str, params=params)
    return BulkImportRequest.from_result(
        client, bulk_import_request_response["createBulkImportRequest"])


def create_from_objects(client, project_id: str, name: str,
                        predictions: Iterable[dict]) -> BulkImportRequest:
    """
    Creates a BulkImportRequest from an iterable of dictionaries conforming to
    JSON predictions format, e.g.:
    ``{
        "uuid": "9fd9a92e-2560-4e77-81d4-b2e955800092",
        "schemaId": "ckappz7d700gn0zbocmqkwd9i",
        "dataRow": {
            "id": "ck1s02fqxm8fi0757f0e6qtdc"
        },
        "bbox": {
            "top": 48,
            "left": 58,
            "height": 865,
            "width": 1512
        }
    }``

    Args:
        client (Client): a Labelbox client
        project_id (str): id of project for which predictions will be imported
        name (str): name of BulkImportRequest
        predictions (Iterable[dict]): iterable of dictionaries representing predictions
    Returns:
        BulkImportRequest object
    """
    data_str = ndjson.dumps(predictions)
    data = data_str.encode('utf-8')
    file_name = __make_file_name(project_id, name)
    request_data = self.__make_request_data(name, len(data_str), file_name)
    file_data = (file_name, data, NDJSON_MIME_TYPE)
    response_data = self.__send_create_file_command(
        request_data=request_data,
        file_name=file_name,
        file_data=file_data)

    return BulkImportRequest.from_result(
        client, response_data["createBulkImportRequest"])


def create_from_local_file(client,
                           project_id: str,
                           name: str,
                           file: Path,
                           validate_file=True) -> BulkImportRequest:
    """
    Creates a BulkImportRequest from a local ndjson file with predictions.

    Args:
        client (Client): a Labelbox client
        project_id (str): id of project for which predictions will be imported
        name (str): name of BulkImportRequest
        file (Path): local ndjson file with predictions
        validate_file (bool): a flag indicating if there should be a validation
            if `file` is a valid ndjson file
    Returns:
        BulkImportRequest object
    """
    file_name = __make_file_name(project_id, name)
    content_length = file.stat().st_size
    request_data = self.__make_request_data(name, content_length, file_name)
    if validate_file:
        with file.open('rb') as f:
            reader = ndjson.reader(f)
            # ensure that the underlying json load call is valid
            # https://github.com/rhgrant10/ndjson/blob/ff2f03c56b21f28f7271b27da35ca4a8bf9a05d0/ndjson/api.py#L53
            # by iterating through the file so we only store
            # each line in memory rather than the entire file
            try:
                for line in reader:
                    pass
            except ValueError:
                raise ValueError(f"{file} is not a valid ndjson file")

    with file.open('rb') as f:
        file_data = (file.name, f, NDJSON_MIME_TYPE)
        response_data = self.__send_create_file_command(
            request_data, file_name, file_data)
    return BulkImportRequest.from_result(
        client, response_data["createBulkImportRequest"])
