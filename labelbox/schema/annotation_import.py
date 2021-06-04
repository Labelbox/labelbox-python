from enum import Enum
import functools
from typing import Any, Dict, List, Type
from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field, Relationship
import requests
import ndjson
from dataclasses import dataclass
import json
from labelbox.orm import query
import os
import logging

NDJSON_MIME_TYPE = "application/x-ndjson"
logger = logging.getLogger(__name__)

#Replacement for bulk_import_request.
# Will not use validation since we will move annotation objects here soon.

class PredictionType(Enum):
    MODEL_ERROR_ANALYSIS = "MODEL_ERROR_ANALYSIS"
    MODEL_ASSISTED_LABELING = "MODEL_ASSISTED_LABELING"


class PredictionImportState(Enum):
    """ State of the import job when importing annotations (RUNNING, FAILED, or FINISHED).

    .. list-table::
       :widths: 15 150
       :header-rows: 1

       * - State
         - Description
       * - RUNNING
         - Indicates that the import job is not done yet.
       * - FAILED
         - Indicates the import job failed. Check `BulkImportRequest.errors` for more information
       * - FINISHED
         - Indicates the import job is no longer running. Check `BulkImportRequest.statuses` for more information
    """
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    FINISHED = "FINISHED"




@dataclass
class PredictionImport(DbObject):
    id_name: str
    prediction_type: PredictionType
    response_key: str


    name = Field.String("name")
    state = Field.Enum(PredictionImportState, "state")
    input_file_url = Field.String("input_file_url")
    error_file_url = Field.String("error_file_url")
    status_file_url = Field.String("status_file_url")

    # TODO: Not sure if this works for MEA
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
            See `BulkImportRequest.statuses` for more details.

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
             - Indicates SUCCESS or FAILURE.
           * - errors
             - An array of error messages included when status is FAILURE. Each error has a name, message and optional (key might not exist) additional_info.

        * This information will expire after 24 hours.
        """
        self.wait_until_done()
        return self._fetch_remote_ndjson(self.status_file_url)

    @functools.lru_cache()
    def _fetch_remote_ndjson(self, url: str) -> List[Dict[str, Any]]:
        """
        Fetches the remote ndjson file and caches the results.

        Args:
            url (str): Can be any url pointing to an ndjson file.
        Returns:
            ndjson as a list of dicts.
        """
        response = requests.get(url)
        response.raise_for_status()
        return ndjson.loads(response.text)

    @staticmethod
    def _validate_obj(cls):
        # TODO: isinstance won't work.. check the type..
        if isinstance(cls, PredictionImport):
            raise TypeError("Cannot diretly instantiate PredictionImport. Must use base class instead")

    fileUrl: "https://drive.google.com/uc?export=download&id=1-jKUx1sM3rwDmSHOM2_y0vvZQjrSDRYe"

    @classmethod
    def _build_import_predictions_query(cls, parent_id : str, name: str, file_args : str):
        cls._validate_obj(cls)


        query_str = """mutation testPredictionImportsPyApi {
        createPredictionImport(data: {
        %s : %s
        name: %s
        %s
        predictionType: %s
        }) {
        __typename
        ... on ModelAssistedLabelingPredictionImport {%s}
        ... on ModelErrorAnalysisPredictionImport {%s}
        }""" % (
            cls.id_name,
            parent_id,
            name,
            cls.prediction_type,
            query.results_query_part(cls),
            query.results_query_part(cls)
        )
        return query_str

    @classmethod
    def _from_name(cls, client, parent_id, name: str):
        cls._validate_obj(cls)
        response = """query
        getImportPyApi {
            predictionImport(where: {%s: %s, name: %s}){%s}""" % (cls.id_name, parent_id, name, query.results_query_part(cls))
        return cls(client, response[cls.response_key])

    @classmethod
    def _create_from_url(cls, client, parent_id, name, url):
        file_args = "fileUrl : %s" % url
        query_str = cls._build_import_predictions_query(client, parent_id, name, file_args)
        response = client.execute(query_str)
        return cls(client, response[cls.response_key])

    @staticmethod
    def _make_file_name(parent_id: str, name: str) -> str:
        return f"{parent_id}__{name}.ndjson"

    @classmethod
    def _create_from_bytes(cls, client, parent_id,name, bytes_data):
        # Copying bulk import request for now
        # TODO: Figure out why it has to be sent like this...
        file_name = cls._make_file_name(parent_id, name)
        file_args = """filePayload: {
                file: $file,
                contentLength: $contentLength
            }"""

        query_str = cls._build_import_predictions_query(client, parent_id, name, file_args)
        operations = json.dumps({"variables": {'file' : None}, "query": query_str})
        data = {
            "operations": operations,
            # This varibles.file isn't going to work. is there an alternative???? Like just setting it to None??
            "map": (None, json.dumps({file_name: ["variables.file"]}))
        }
        file_name = cls._make_file_name(parent_id, name)
        file_data = (file_name, bytes_data, NDJSON_MIME_TYPE)
        files = {file_name: file_data}
        response = client.execute(data = data, files = files)
        return cls(client, response[cls.response_key])

    @classmethod
    def _create_from_objects(cls, client, parent_id, name, predictions):
        data_str = ndjson.dumps(predictions)
        if not data_str:
            raise ValueError('annotations cannot be empty')
        data = data_str.encode('utf-8')
        return cls._create_from_bytes(client, parent_id, name, data)

    @classmethod
    def _create_from_file(cls, client, parent_id, name, path):
        if os.path.exists(path):
            with open(path, 'rb') as f:
                return cls._create_from_bytes(client, parent_id,name, f)
        elif requests.head(path):
            return cls._create_from_url(client, parent_id, name, path)
        raise ValueError(f"Path {path} is not accessible locally or on a remote server")

    def create_from_objects(cls):
        raise NotImplementedError("")

    def create_from_file(cls):
        # Handles both url and local files. Does that make sense?
        raise NotImplementedError("")


class MEAPredictionImport(PredictionImport):
    project = Relationship.ToOne("Project")

    id_name = "modelRunId"
    prediction_type = PredictionType.MODEL_ERROR_ANALYSIS

    def create_from_file(cls, client, model_run_id, path):
        return cls.create_from_file(client = client, parent_id = model_run_id, path = path)

    def create_from_objects(cls, client, project_id, name, predictions):
        return cls._create_from_objects(client, project_id, name, predictions)

class MALPredictionImport(PredictionImport):
    id_name = "projectId"
    prediction_type = PredictionType.MODEL_ERROR_ANALYSIS

    # TODO: Not sure if this works for MEA
    model_run = Relationship.ToOne("ModelRun")

    def create_from_file(cls, client, project_id, path):
        return cls.create_from_file(client = client, parent_id = project_id, path = path)

    def create_from_objects(cls, client, project_id, name, predictions):
        return cls._create_from_objects(client, project_id, name, predictions)

