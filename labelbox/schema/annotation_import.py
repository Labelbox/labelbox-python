from enum import Enum
from labelbox.schema.enums import AnnotationImportState, ImportType
from typing import Any, Dict, List
import functools
import os
import json
import time
import logging

import backoff
import ndjson
import requests

import labelbox
from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field, Relationship
from labelbox.orm import query

NDJSON_MIME_TYPE = "application/x-ndjson"
logger = logging.getLogger(__name__)


class AnnotationImport(DbObject):
    # This class will replace BulkImportRequest.
    # Currently this exists for the MEA beta.
    # Use BulkImportRequest for now if you are not using MEA.

    id_name: str
    import_type: ImportType

    name = Field.String("name")
    state = Field.Enum(AnnotationImportState, "state")
    input_file_url = Field.String("input_file_url")
    error_file_url = Field.String("error_file_url")
    status_file_url = Field.String("status_file_url")

    created_by = Relationship.ToOne("User", False, "created_by")

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

    @classmethod
    def _build_import_predictions_query(cls, file_args: str, vars: str):
        cls.validate_cls()
        query_str = """mutation createAnnotationImportPyApi($parent_id : ID!, $name: String!, $predictionType : PredictionType!, %s) {
        createAnnotationImport(data: {
            %s : $parent_id
            name: $name
            %s
            predictionType: $predictionType
        }) {
        __typename
        ... on ModelAssistedLabelingPredictionImport {%s}
        ... on ModelErrorAnalysisPredictionImport {%s}
        }}""" % (vars, cls.id_name, file_args,
                 query.results_query_part(MALPredictionImport),
                 query.results_query_part(MEAPredictionImport))
        return query_str

    @classmethod
    def validate_cls(cls):
        supported_base_classes = {MALPredictionImport, MEAPredictionImport}
        if cls not in {MALPredictionImport, MEAPredictionImport}:
            raise TypeError(
                f"Can't directly use the base AnnotationImport class. Must use one of {supported_base_classes}"
            )

    @classmethod
    def from_name(cls, client, parent_id, name: str, raw=False):
        cls.validate_cls()
        query_str = """query getImportPyApi($parent_id : ID!, $name: String!) {
            annotationImport(
                where: {%s: $parent_id, name: $name}){
                    __typename
                ... on ModelAssistedLabelingPredictionImport {%s}
                ... on ModelErrorAnalysisPredictionImport {%s}
                }}""" % \
                (
                    cls.id_name,
                    query.results_query_part(MALPredictionImport),
                    query.results_query_part(MEAPredictionImport)
        )

        response = client.execute(query_str, {
            'name': name,
            'parent_id': parent_id
        })
        if raw:
            return response['annotationImport']

        return cls(client, response['annotationImport'])

    @classmethod
    def _create_from_url(cls, client, parent_id, name, url):
        file_args = "fileUrl : $fileUrl"
        query_str = cls._build_import_predictions_query(file_args,
                                                        "$fileUrl: String!")
        response = client.execute(query_str,
                                  params={
                                      "fileUrl": url,
                                      "parent_id": parent_id,
                                      'name': name,
                                      'predictionType': cls.import_type.value
                                  })
        return cls(client, response['createAnnotationImport'])

    @staticmethod
    def _make_file_name(parent_id: str, name: str) -> str:
        return f"{parent_id}__{name}.ndjson"

    def refresh(self) -> None:
        """Synchronizes values of all fields with the database.
        """
        cls = type(self)
        res = cls.from_name(self.client,
                            self.get_parent_id(),
                            self.name,
                            raw=True)
        self._set_field_values(res)

    @classmethod
    def _create_from_bytes(cls, client, parent_id, name, bytes_data,
                           content_len):
        file_name = cls._make_file_name(parent_id, name)
        file_args = """filePayload: {
                file: $file,
                contentLength: $contentLength
            }"""
        query_str = cls._build_import_predictions_query(
            file_args, "$file: Upload!, $contentLength: Int!")
        variables = {
            "file": None,
            "contentLength": content_len,
            "parent_id": parent_id,
            "name": name,
            "predictionType": cls.import_type.value
        }
        operations = json.dumps({"variables": variables, "query": query_str})
        data = {
            "operations": operations,
            "map": (None, json.dumps({file_name: ["variables.file"]}))
        }
        file_data = (file_name, bytes_data, NDJSON_MIME_TYPE)
        files = {file_name: file_data}

        response = client.execute(data=data, files=files)
        return cls(client, response['createAnnotationImport'])

    @classmethod
    def _create_from_objects(cls, client, parent_id, name, predictions):
        data_str = ndjson.dumps(predictions)
        if not data_str:
            raise ValueError('annotations cannot be empty')
        data = data_str.encode('utf-8')
        return cls._create_from_bytes(client, parent_id, name, data, len(data))

    @classmethod
    def _create_from_file(cls, client, parent_id, name, path):
        if os.path.exists(path):
            with open(path, 'rb') as f:
                return cls._create_from_bytes(client, parent_id, name, f,
                                              os.stat(path).st_size)
        elif requests.head(path):
            return cls._create_from_url(client, parent_id, name, path)
        raise ValueError(
            f"Path {path} is not accessible locally or on a remote server")

    def create_from_objects(*args, **kwargs):
        raise NotImplementedError("")

    def create_from_file(*args, **kwargs):
        raise NotImplementedError("")

    def get_parent_id(*args, **kwargs):
        raise NotImplementedError("")


class MEAPredictionImport(AnnotationImport):
    id_name = "modelRunId"
    import_type = ImportType.MODEL_ERROR_ANALYSIS
    model_run_id = Field.String("model_run_id")

    def get_parent_id(self):
        return self.model_run_id

    @classmethod
    def create_from_file(cls, client, model_run_id, name, path):
        return cls._create_from_file(client=client,
                                     parent_id=model_run_id,
                                     name=name,
                                     path=path)

    @classmethod
    def create_from_objects(cls, client, model_run_id, name, predictions):
        return cls._create_from_objects(client, model_run_id, name, predictions)


class MALPredictionImport(AnnotationImport):
    id_name = "projectId"
    import_type = ImportType.MODEL_ASSISTED_LABELING
    project = Relationship.ToOne("Project", cache=True)

    def get_parent_id(self):
        return self.project().uid

    @classmethod
    def create_from_file(cls, client, project_id, name, path):
        return cls._create_from_file(client=client,
                                     parent_id=project_id,
                                     name=name,
                                     path=path)

    @classmethod
    def create_from_objects(cls, client, project_id, name, predictions):
        return cls._create_from_objects(client, project_id, name, predictions)
