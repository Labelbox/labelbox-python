from typing import Any, Dict, List, Union
import functools
import os
import json
import time
import logging

import backoff
import ndjson
import requests

import labelbox
from labelbox.schema.enums import AnnotationImportState
from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field, Relationship
from labelbox.orm import query

NDJSON_MIME_TYPE = "application/x-ndjson"
logger = logging.getLogger(__name__)


class AnnotationImport(DbObject):
    name = Field.String("name")
    state = Field.Enum(AnnotationImportState, "state")
    input_file_url = Field.String("input_file_url")
    error_file_url = Field.String("error_file_url")
    status_file_url = Field.String("status_file_url")

    created_by = Relationship.ToOne("User", False, "created_by")

    parent_id: str
    _mutation: str
    _parent_id_field: str

    @property
    def inputs(self) -> List[Dict[str, Any]]:
        """
        Inputs for each individual annotation uploaded.
        This should match the ndjson annotations that you have uploaded.
        Returns:
            Uploaded ndjson.
        * This information will expire after 24 hours.
        """
        return self._fetch_remote_ndjson(self.input_file_url)

    @property
    def errors(self) -> List[Dict[str, Any]]:
        """
        Errors for each individual annotation uploaded. This is a subset of statuses
        Returns:
            List of dicts containing error messages. Empty list means there were no errors
            See `AnnotationImport.statuses` for more details.
        * This information will expire after 24 hours.
        """
        self.wait_until_done()
        return self._fetch_remote_ndjson(self.error_file_url)

    @property
    def statuses(self) -> List[Dict[str, Any]]:
        """
        Status for each individual annotation uploaded.
        Returns:
            A status for each annotation if the upload is done running.
            See below table for more details
        .. list-table::
           :widths: 15 150
           :header-rows: 1
           * - Field
             - Description
           * - uuid
             - Specifies the annotation for the status row.
           * - dataRow
             - JSON object containing the Labelbox data row ID for the annotation.
           * - status
             - Indicates SUCCESS or FAILURE.
           * - errors
             - An array of error messages included when status is FAILURE. Each error has a name, message and optional (key might not exist) additional_info.
        * This information will expire after 24 hours.
        """
        self.wait_until_done()
        return self._fetch_remote_ndjson(self.status_file_url)

    def wait_until_done(self, sleep_time_seconds: int = 10) -> None:
        """Blocks import job until certain conditions are met.
        Blocks until the AnnotationImport.state changes either to
        `AnnotationImportState.FINISHED` or `AnnotationImportState.FAILED`,
        periodically refreshing object's state.
        Args:
            sleep_time_seconds (str): a time to block between subsequent API calls
        """
        while self.state.value == AnnotationImportState.RUNNING.value:
            logger.info(f"Sleeping for {sleep_time_seconds} seconds...")
            time.sleep(sleep_time_seconds)
            self.__backoff_refresh()

    @backoff.on_exception(
        backoff.expo,
        (labelbox.exceptions.ApiLimitError, labelbox.exceptions.TimeoutError,
         labelbox.exceptions.NetworkError),
        max_tries=10,
        jitter=None)
    def __backoff_refresh(self) -> None:
        self.refresh()

    @functools.lru_cache()
    def _fetch_remote_ndjson(self, url: str) -> List[Dict[str, Any]]:
        """
        Fetches the remote ndjson file and caches the results.
        Args:
            url (str): Can be any url pointing to an ndjson file.
        Returns:
            ndjson as a list of dicts.
        """
        if self.state == AnnotationImportState.FAILED:
            raise ValueError("Import failed.")

        response = requests.get(url)
        response.raise_for_status()
        return ndjson.loads(response.text)

    @staticmethod
    def _make_file_name(parent_id: str, name: str) -> str:
        return f"{parent_id}__{name}.ndjson"

    def refresh(self) -> None:
        """Synchronizes values of all fields with the database.
        """
        cls = type(self)
        res = cls._from_name(self.client, self.parent_id, self.name, raw=True)
        self._set_field_values(res)

    @classmethod
    def _create_from_bytes(
        cls, client: "labelbox.Client", parent_id: str, name: str,
        bytes_data: bytes, content_len: int
    ) -> Union["MEAPredictionImport", "MALPredictionImport"]:
        file_name = cls._make_file_name(parent_id, name)
        variables = {
            "file": None,
            "contentLength": content_len,
            "parentId": parent_id,
            "name": name
        }
        query_str = cls._get_file_mutation()
        operations = json.dumps({"variables": variables, "query": query_str})
        data = {
            "operations": operations,
            "map": (None, json.dumps({file_name: ["variables.file"]}))
        }
        file_data = (file_name, bytes_data, NDJSON_MIME_TYPE)
        files = {file_name: file_data}
        return cls(client,
                   client.execute(data=data, files=files)[cls._mutation])

    @classmethod
    def _create_from_objects(
        cls, client: "labelbox.Client", parent_id: str, name: str,
        predictions: List[Dict[str, Any]]
    ) -> Union["MEAPredictionImport", "MALPredictionImport"]:
        data_str = ndjson.dumps(predictions)
        if not data_str:
            raise ValueError('annotations cannot be empty')
        data = data_str.encode('utf-8')
        return cls._create_from_bytes(client, parent_id, name, data, len(data))

    @classmethod
    def _create_from_url(
            cls, client: "labelbox.Client", parent_id: str, name: str,
            url: str) -> Union["MEAPredictionImport", "MALPredictionImport"]:
        if requests.head(url):
            query_str = cls._get_url_mutation()
            return cls(
                client,
                client.execute(query_str,
                               params={
                                   "fileUrl": url,
                                   "parentId": parent_id,
                                   'name': name
                               })[cls._mutation])
        else:
            raise ValueError(f"Url {url} is not reachable")

    @classmethod
    def _create_from_file(
            cls, client: "labelbox.Client", parent_id: str, name: str,
            path: str) -> Union["MEAPredictionImport", "MALPredictionImport"]:
        if os.path.exists(path):
            with open(path, 'rb') as f:
                return cls._create_from_bytes(client, parent_id, name, f,
                                              os.stat(path).st_size)
        else:
            raise ValueError(f"File {path} is not accessible")

    @classmethod
    def _get_url_mutation(cls) -> str:
        return """mutation create%sPyApi($parentId : ID!, $name: String!, $fileUrl: String!) {
            %s(data: {
                %s: $parentId
                name: $name
                fileUrl: $fileUrl
            }) {%s}
        }""" % (cls.__class__.__name__, cls._mutation, cls._parent_id_field,
                query.results_query_part(cls))

    @classmethod
    def _get_file_mutation(cls) -> str:
        return """mutation create%sPyApi($parentId : ID!, $name: String!, $file: Upload!, $contentLength: Int!) {
            %s(data: { %s : $parentId name: $name filePayload: { file: $file, contentLength: $contentLength}
        }) {%s}
        }""" % (cls.__class__.__name__, cls._mutation, cls._parent_id_field,
                query.results_query_part(cls))


class MEAPredictionImport(AnnotationImport):
    model_run_id = Field.String("model_run_id")
    _mutation = "createModelErrorAnalysisPredictionImport"
    _parent_id_field = "modelRunId"

    @property
    def parent_id(self) -> str:
        return self.model_run_id

    @classmethod
    def create_from_file(cls, client: "labelbox.Client", model_run_id: str,
                         name: str, path: str) -> "MEAPredictionImport":
        return cls._create_from_file(client=client,
                                     parent_id=model_run_id,
                                     name=name,
                                     path=path)

    @classmethod
    def create_from_objects(cls, client: "labelbox.Client", model_run_id: str,
                            name, predictions) -> "MEAPredictionImport":
        return cls._create_from_objects(client, model_run_id, name, predictions)

    @classmethod
    def create_from_url(cls, client: "labelbox.Client", model_run_id: str,
                        name: str, url: str) -> "MEAPredictionImport":
        return cls._create_from_url(client=client,
                                    parent_id=model_run_id,
                                    name=name,
                                    url=url)
                                    
    @classmethod
    def from_name(
            cls, client: "labelbox.Client", model_run_id: str,
            name: str) -> "MEAPredictionImport":

        query_str = """query getModelErrorAnalysisPredictionImportPyApi($modelRunId : ID!, $name: String!) {
            modelErrorAnalysisPredictionImport(
                where: {modelRunId: $modelRunId, name: $name}){
                    %s
                }}""" % query.results_query_part(cls)
        params = {
            "modelRunId": model_run_id,
            "name": name,
        }
        response = client.execute(query_str, params)
        if response is None: 
           raise labelbox.exceptions.ResourceNotFoundError(MEAPredictionImport, params)

        return response


class MALPredictionImport(AnnotationImport):
    project = Relationship.ToOne("Project", cache=True)
    _mutation = "createModelAssistedLabelingPredictionImport"
    _parent_id_field = "projectId"

    @property
    def parent_id(self) -> str:
        return self.project().uid

    @classmethod
    def create_from_file(cls, client: "labelbox.Client", project_id: str,
                         name: str, path: str) -> "MALPredictionImport":
        return cls._create_from_file(client=client,
                                     parent_id=project_id,
                                     name=name,
                                     path=path)

    @classmethod
    def create_from_objects(cls, client: "labelbox.Client", project_id: str,
                            name, predictions) -> "MALPredictionImport":
        return cls._create_from_objects(client, project_id, name, predictions)

    @classmethod
    def create_from_url(cls, client: "labelbox.Client", project_id: str,
                        name: str, url: str) -> "MALPredictionImport":
        return cls._create_from_url(client=client,
                                    parent_id=project_id,
                                    name=name,
                                    url=url)

    @classmethod
    def from_name(
            cls, client: "labelbox.Client", project_id: str,
            name: str) -> "MALPredictionImport":

        query_str = """query getModelAssistedLabelingPredictionImportPyApi($projectId : ID!, $name: String!) {
            modelAssistedLabelingPredictionImport(
                where: {projectId: $projectId, name: $name}){
                    %s
                }}""" % query.results_query_part(cls)
        params = {
            "projectId": project_id,
            "name": name,
        }
        response = client.execute(query_str, params)
        if response is None: 
           raise labelbox.exceptions.ResourceNotFoundError(MALPredictionImport, params)

        return response
