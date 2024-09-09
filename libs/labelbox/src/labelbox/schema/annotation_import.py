import functools
import json
import logging
import os
import time
from typing import Any, BinaryIO, Dict, List, Optional, Union, TYPE_CHECKING, cast
from collections import defaultdict

from google.api_core import retry
from labelbox import parser
import requests
from tqdm import tqdm  # type: ignore

import labelbox
from labelbox.orm import query
from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field, Relationship
from labelbox.utils import is_exactly_one_set
from labelbox.schema.confidence_presence_checker import LabelsConfidencePresenceChecker
from labelbox.schema.enums import AnnotationImportState
from labelbox.schema.serialization import serialize_labels

if TYPE_CHECKING:
    from labelbox.types import Label

NDJSON_MIME_TYPE = "application/x-ndjson"
ANNOTATION_PER_LABEL_LIMIT = 5000

logger = logging.getLogger(__name__)


class AnnotationImport(DbObject):
    name = Field.String("name")
    state = Field.Enum(AnnotationImportState, "state")
    input_file_url = Field.String("input_file_url")
    error_file_url = Field.String("error_file_url")
    status_file_url = Field.String("status_file_url")
    progress = Field.String("progress")

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

    def wait_till_done(self,
                        sleep_time_seconds: int = 10,
                        show_progress: bool = False) -> None:
        self.wait_until_done(sleep_time_seconds, show_progress)

    def wait_until_done(self,
                        sleep_time_seconds: int = 10,
                        show_progress: bool = False) -> None:
        """Blocks import job until certain conditions are met.
        Blocks until the AnnotationImport.state changes either to
        `AnnotationImportState.FINISHED` or `AnnotationImportState.FAILED`,
        periodically refreshing object's state.
        Args:
            sleep_time_seconds (int): a time to block between subsequent API calls
            show_progress (bool): should show progress bar
        """
        pbar = tqdm(total=100,
                    bar_format="{n}% |{bar}| [{elapsed}, {rate_fmt}{postfix}]"
                   ) if show_progress else None
        while self.state.value == AnnotationImportState.RUNNING.value:
            logger.info(f"Sleeping for {sleep_time_seconds} seconds...")
            time.sleep(sleep_time_seconds)
            self.__backoff_refresh()
            if self.progress and self.progress and pbar:
                pbar.update(int(self.progress.replace("%", "")) - pbar.n)

        if pbar:
            pbar.update(100 - pbar.n)
            pbar.close()

    @retry.Retry(predicate=retry.if_exception_type(
        labelbox.exceptions.ApiLimitError, labelbox.exceptions.TimeoutError,
        labelbox.exceptions.NetworkError))
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
        return parser.loads(response.text)

    @classmethod
    def _create_from_bytes(cls, client, variables, query_str, file_name,
                           bytes_data) -> Dict[str, Any]:
        operations = json.dumps({"variables": variables, "query": query_str})
        data = {
            "operations": operations,
            "map": (None, json.dumps({file_name: ["variables.file"]}))
        }
        file_data = (file_name, bytes_data, NDJSON_MIME_TYPE)
        files = {file_name: file_data}
        return client.execute(data=data, files=files)

    @classmethod
    def _get_ndjson_from_objects(cls, objects: Union[List[Dict[str, Any]],
                                                     List["Label"]],
                                 object_name: str) -> BinaryIO:
        if not isinstance(objects, list):
            raise TypeError(
                f"{object_name} must be in a form of list. Found {type(objects)}"
            )

        objects = serialize_labels(objects)
        cls._validate_data_rows(objects)

        data_str = parser.dumps(objects)
        if not data_str:
            raise ValueError(f"{object_name} cannot be empty")

        return data_str.encode(
            'utf-8'
        )  # NOTICE this method returns bytes, NOT BinaryIO... should have done  io.BytesIO(...) but not going to change this at the moment since it works and fools mypy

    def refresh(self) -> None:
        """Synchronizes values of all fields with the database.
        """
        cls = type(self)
        res = cls.from_name(self.client,
                            self.parent_id,
                            self.name,
                            as_json=True)
        self._set_field_values(res)

    @classmethod
    def _validate_data_rows(cls, objects: List[Dict[str, Any]]):
        """
        Validates annotations by checking 'dataRow' is provided
        and only one of 'id' or 'globalKey' is provided.

        Shows up to `max_num_errors` errors if invalidated, to prevent
        large number of error messages from being printed out 
        """
        errors = []
        max_num_errors = 100
        labels_per_datarow: Dict[str, Dict[str, int]] = defaultdict(
            lambda: defaultdict(int))
        for object in objects:
            if 'dataRow' not in object:
                errors.append(f"'dataRow' is missing in {object}")
                continue
            data_row_object = object['dataRow']
            if not is_exactly_one_set(data_row_object.get('id'),
                                      data_row_object.get('globalKey')):
                errors.append(
                    f"Must provide only one of 'id' or 'globalKey' for 'dataRow' in {object}"
                )
            else:
                data_row_id = data_row_object.get(
                    'globalKey') or data_row_object.get('id')
                name = object.get('name')
                if name:
                    labels_per_datarow[data_row_id][name] += 1
        for data_row_id, label_annotations in labels_per_datarow.items():
            for label_name, annotations in label_annotations.items():
                if annotations > ANNOTATION_PER_LABEL_LIMIT:
                    errors.append(
                        f"Row with id or global key {data_row_id} has {annotations} annotations for label {label_name}.\
                              Imports are limited to {ANNOTATION_PER_LABEL_LIMIT} annotations per data row."
                    )
        if errors:
            errors_length = len(errors)
            formatted_errors = '\n'.join(errors[:max_num_errors])
            if errors_length > max_num_errors:
                logger.warning(
                    f"Found more than {max_num_errors} errors. Showing first {max_num_errors} error messages..."
                )
            raise ValueError(
                f"Error while validating annotations. Found {errors_length} annotations with errors. Errors:\n{formatted_errors}"
            )

    @classmethod
    def from_name(cls,
                  client: "labelbox.Client",
                  parent_id: str,
                  name: str,
                  as_json: bool = False):
        raise NotImplementedError("Inheriting class must override")

    @property
    def parent_id(self) -> str:
        raise NotImplementedError("Inheriting class must override")


class CreatableAnnotationImport(AnnotationImport):

    @classmethod
    def create(
        cls,
        client: "labelbox.Client",
        id: str,
        name: str,
        path: Optional[str] = None,
        url: Optional[str] = None,
        labels: Union[List[Dict[str, Any]], List["Label"]] = []
    ) -> "AnnotationImport":
        if (not is_exactly_one_set(url, labels, path)):
            raise ValueError(
                "Must pass in a nonempty argument for one and only one of the following arguments: url, path, predictions"
            )
        if url:
            return cls.create_from_url(client, id, name, url)
        if path:
            return cls.create_from_file(client, id, name, path)
        return cls.create_from_objects(client, id, name, labels)

    @classmethod
    def create_from_url(cls, client: "labelbox.Client", id: str, name: str,
                        url: str) -> "AnnotationImport":
        raise NotImplementedError("Inheriting class must override")

    @classmethod
    def create_from_file(cls, client: "labelbox.Client", id: str, name: str,
                         path: str) -> "AnnotationImport":
        raise NotImplementedError("Inheriting class must override")

    @classmethod
    def create_from_objects(
        cls, client: "labelbox.Client", id: str, name: str,
        labels: Union[List[Dict[str, Any]],
                      List["Label"]]) -> "AnnotationImport":
        raise NotImplementedError("Inheriting class must override")


class MEAPredictionImport(CreatableAnnotationImport):
    model_run_id = Field.String("model_run_id")

    @property
    def parent_id(self) -> str:
        """
        Identifier for this import. Used to refresh the status
        """
        return self.model_run_id

    @classmethod
    def create_from_file(cls, client: "labelbox.Client", model_run_id: str,
                         name: str, path: str) -> "MEAPredictionImport":
        """
        Create an MEA prediction import job from a file of annotations

        Args:
            client: Labelbox Client for executing queries
            model_run_id: Model run to import labels into
            name: Name of the import job. Can be used to reference the task later
            path: Path to ndjson file containing annotations
        Returns:
            MEAPredictionImport
        """
        if os.path.exists(path):
            with open(path, 'rb') as f:
                return cls._create_mea_import_from_bytes(
                    client, model_run_id, name, f,
                    os.stat(path).st_size)
        else:
            raise ValueError(f"File {path} is not accessible")

    @classmethod
    def create_from_objects(
        cls, client: "labelbox.Client", model_run_id: str, name,
        predictions: Union[List[Dict[str, Any]], List["Label"]]
    ) -> "MEAPredictionImport":
        """
        Create an MEA prediction import job from an in memory dictionary

        Args:
            client: Labelbox Client for executing queries
            model_run_id: Model run to import labels into
            name: Name of the import job. Can be used to reference the task later
            predictions: List of prediction annotations
        Returns:
            MEAPredictionImport
        """
        data = cls._get_ndjson_from_objects(predictions, 'annotations')

        return cls._create_mea_import_from_bytes(client, model_run_id, name,
                                                 data, len(str(data)))

    @classmethod
    def create_from_url(cls, client: "labelbox.Client", model_run_id: str,
                        name: str, url: str) -> "MEAPredictionImport":
        """
        Create an MEA prediction import job from a url
        The url must point to a file containing prediction annotations.

        Args:
            client: Labelbox Client for executing queries
            model_run_id: Model run to import labels into
            name: Name of the import job. Can be used to reference the task later
            url: Url pointing to file to upload
        Returns:
            MEAPredictionImport
        """
        if requests.head(url):
            query_str = cls._get_url_mutation()
            return cls(
                client,
                client.execute(query_str,
                               params={
                                   "fileUrl": url,
                                   "modelRunId": model_run_id,
                                   'name': name
                               })["createModelErrorAnalysisPredictionImport"])
        else:
            raise ValueError(f"Url {url} is not reachable")

    @classmethod
    def from_name(cls,
                  client: "labelbox.Client",
                  model_run_id: str,
                  name: str,
                  as_json: bool = False) -> "MEAPredictionImport":
        """
        Retrieves an MEA import job.

        Args:
            client: Labelbox Client for executing queries
            model_run_id: ID used for querying import jobs
            name: Name of the import job.
        Returns:
            MEAPredictionImport
        """
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
            raise labelbox.exceptions.ResourceNotFoundError(
                MEAPredictionImport, params)
        response = response["modelErrorAnalysisPredictionImport"]
        if as_json:
            return response
        return cls(client, response)

    @classmethod
    def _get_url_mutation(cls) -> str:
        return """mutation createMEAPredictionImportByUrlPyApi($modelRunId : ID!, $name: String!, $fileUrl: String!) {
            createModelErrorAnalysisPredictionImport(data: {
                modelRunId: $modelRunId
                name: $name
                fileUrl: $fileUrl
            }) {%s}
        }""" % query.results_query_part(cls)

    @classmethod
    def _get_file_mutation(cls) -> str:
        return """mutation createMEAPredictionImportByFilePyApi($modelRunId : ID!, $name: String!, $file: Upload!, $contentLength: Int!) {
            createModelErrorAnalysisPredictionImport(data: {
                modelRunId: $modelRunId name: $name filePayload: { file: $file, contentLength: $contentLength}
        }) {%s}
        }""" % query.results_query_part(cls)

    @classmethod
    def _create_mea_import_from_bytes(
            cls, client: "labelbox.Client", model_run_id: str, name: str,
            bytes_data: BinaryIO, content_len: int) -> "MEAPredictionImport":
        file_name = f"{model_run_id}__{name}.ndjson"
        variables = {
            "file": None,
            "contentLength": content_len,
            "modelRunId": model_run_id,
            "name": name
        }
        query_str = cls._get_file_mutation()
        res = cls._create_from_bytes(
            client,
            variables,
            query_str,
            file_name,
            bytes_data,
        )
        return cls(client, res["createModelErrorAnalysisPredictionImport"])


class MEAToMALPredictionImport(AnnotationImport):
    project = Relationship.ToOne("Project", cache=True)

    @property
    def parent_id(self) -> str:
        """
        Identifier for this import. Used to refresh the status
        """
        return self.project().uid

    @classmethod
    def create_for_model_run_data_rows(cls, client: "labelbox.Client",
                                       model_run_id: str,
                                       data_row_ids: List[str], project_id: str,
                                       name: str) -> "MEAToMALPredictionImport":
        """
        Create an MEA to MAL prediction import job from a list of data row ids of a specific model run

        Args:
            client: Labelbox Client for executing queries
            data_row_ids: A list of data row ids
            model_run_id: model run id
        Returns:
            MEAToMALPredictionImport
        """
        query_str = cls._get_model_run_data_rows_mutation()
        return cls(
            client,
            client.execute(query_str,
                           params={
                               "dataRowIds": data_row_ids,
                               "modelRunId": model_run_id,
                               "projectId": project_id,
                               "name": name
                           })["createMalPredictionImportForModelRunDataRows"])

    @classmethod
    def from_name(cls,
                  client: "labelbox.Client",
                  project_id: str,
                  name: str,
                  as_json: bool = False) -> "MEAToMALPredictionImport":
        """
        Retrieves an MEA to MAL import job.

        Args:
            client: Labelbox Client for executing queries
            project_id:  ID used for querying import jobs
            name: Name of the import job.
        Returns:
            MALPredictionImport
        """
        query_str = """query getMEAToMALPredictionImportPyApi($projectId : ID!, $name: String!) {
            meaToMalPredictionImport(
                where: {projectId: $projectId, name: $name}){
                    %s
                }}""" % query.results_query_part(cls)
        params = {
            "projectId": project_id,
            "name": name,
        }
        response = client.execute(query_str, params)
        if response is None:
            raise labelbox.exceptions.ResourceNotFoundError(
                MALPredictionImport, params)
        response = response["meaToMalPredictionImport"]
        if as_json:
            return response
        return cls(client, response)

    @classmethod
    def _get_model_run_data_rows_mutation(cls) -> str:
        return """mutation createMalPredictionImportForModelRunDataRowsPyApi($dataRowIds: [ID!]!, $name: String!, $modelRunId: ID!, $projectId:ID!) {
            createMalPredictionImportForModelRunDataRows(data: {
                name: $name
                modelRunId: $modelRunId
                dataRowIds: $dataRowIds
                projectId: $projectId
            }) {%s}
        }""" % query.results_query_part(cls)


class MALPredictionImport(CreatableAnnotationImport):
    project = Relationship.ToOne("Project", cache=True)

    @property
    def parent_id(self) -> str:
        """
        Identifier for this import. Used to refresh the status
        """
        return self.project().uid

    @classmethod
    def create_from_file(cls, client: "labelbox.Client", project_id: str,
                         name: str, path: str) -> "MALPredictionImport":
        """
        Create an MAL prediction import job from a file of annotations

        Args:
            client: Labelbox Client for executing queries
            project_id: Project to import labels into
            name: Name of the import job. Can be used to reference the task later
            path: Path to ndjson file containing annotations
        Returns:
            MALPredictionImport
        """
        if os.path.exists(path):
            with open(path, 'rb') as f:
                return cls._create_mal_import_from_bytes(
                    client, project_id, name, f,
                    os.stat(path).st_size)
        else:
            raise ValueError(f"File {path} is not accessible")

    @classmethod
    def create_from_objects(
        cls, client: "labelbox.Client", project_id: str, name: str,
        predictions: Union[List[Dict[str, Any]], List["Label"]]
    ) -> "MALPredictionImport":
        """
        Create an MAL prediction import job from an in memory dictionary

        Args:
            client: Labelbox Client for executing queries
            project_id: Project to import labels into
            name: Name of the import job. Can be used to reference the task later
            predictions: List of prediction annotations
        Returns:
            MALPredictionImport
        """

        data = cls._get_ndjson_from_objects(predictions, 'annotations')
        if len(predictions) > 0 and isinstance(predictions[0], Dict):
            predictions_dicts = cast(List[Dict[str, Any]], predictions)
            has_confidence = LabelsConfidencePresenceChecker.check(
                predictions_dicts)
            if has_confidence:
                logger.warning("""
                Confidence scores are not supported in MAL Prediction Import.
                Corresponding confidence score values will be ignored.
                """)
        return cls._create_mal_import_from_bytes(client, project_id, name, data,
                                                 len(str(data)))

    @classmethod
    def create_from_url(cls, client: "labelbox.Client", project_id: str,
                        name: str, url: str) -> "MALPredictionImport":
        """
        Create an MAL prediction import job from a url
        The url must point to a file containing prediction annotations.

        Args:
            client: Labelbox Client for executing queries
            project_id: Project to import labels into
            name: Name of the import job. Can be used to reference the task later
            url: Url pointing to file to upload
        Returns:
            MALPredictionImport
        """
        if requests.head(url):
            query_str = cls._get_url_mutation()
            return cls(
                client,
                client.execute(
                    query_str,
                    params={
                        "fileUrl": url,
                        "projectId": project_id,
                        'name': name
                    })["createModelAssistedLabelingPredictionImport"])
        else:
            raise ValueError(f"Url {url} is not reachable")

    @classmethod
    def from_name(cls,
                  client: "labelbox.Client",
                  project_id: str,
                  name: str,
                  as_json: bool = False) -> "MALPredictionImport":
        """
        Retrieves an MAL import job.

        Args:
            client: Labelbox Client for executing queries
            project_id:  ID used for querying import jobs
            name: Name of the import job.
        Returns:
            MALPredictionImport
        """
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
            raise labelbox.exceptions.ResourceNotFoundError(
                MALPredictionImport, params)
        response = response["modelAssistedLabelingPredictionImport"]
        if as_json:
            return response
        return cls(client, response)

    @classmethod
    def _get_url_mutation(cls) -> str:
        return """mutation createMALPredictionImportByUrlPyApi($projectId : ID!, $name: String!, $fileUrl: String!) {
            createModelAssistedLabelingPredictionImport(data: {
                projectId: $projectId
                name: $name
                fileUrl: $fileUrl
            }) {%s}
        }""" % query.results_query_part(cls)

    @classmethod
    def _get_file_mutation(cls) -> str:
        return """mutation createMALPredictionImportByFilePyApi($projectId : ID!, $name: String!, $file: Upload!, $contentLength: Int!) {
            createModelAssistedLabelingPredictionImport(data: {
                projectId: $projectId name: $name filePayload: { file: $file, contentLength: $contentLength}
        }) {%s}
        }""" % query.results_query_part(cls)

    @classmethod
    def _create_mal_import_from_bytes(
            cls, client: "labelbox.Client", project_id: str, name: str,
            bytes_data: BinaryIO, content_len: int) -> "MALPredictionImport":
        file_name = f"{project_id}__{name}.ndjson"
        variables = {
            "file": None,
            "contentLength": content_len,
            "projectId": project_id,
            "name": name
        }
        query_str = cls._get_file_mutation()
        res = cls._create_from_bytes(client, variables, query_str, file_name,
                                     bytes_data)
        return cls(client, res["createModelAssistedLabelingPredictionImport"])


class LabelImport(CreatableAnnotationImport):
    project = Relationship.ToOne("Project", cache=True)

    @property
    def parent_id(self) -> str:
        """
        Identifier for this import. Used to refresh the status
        """
        return self.project().uid

    @classmethod
    def create_from_file(cls, client: "labelbox.Client", project_id: str,
                         name: str, path: str) -> "LabelImport":
        """
        Create a label import job from a file of annotations

        Args:
            client: Labelbox Client for executing queries
            project_id: Project to import labels into
            name: Name of the import job. Can be used to reference the task later
            path: Path to ndjson file containing annotations
        Returns:
            LabelImport
        """
        if os.path.exists(path):
            with open(path, 'rb') as f:
                return cls._create_label_import_from_bytes(
                    client, project_id, name, f,
                    os.stat(path).st_size)
        else:
            raise ValueError(f"File {path} is not accessible")

    @classmethod
    def create_from_objects(
            cls, client: "labelbox.Client", project_id: str, name: str,
            labels: Union[List[Dict[str, Any]],
                          List["Label"]]) -> "LabelImport":
        """
        Create a label import job from an in memory dictionary

        Args:
            client: Labelbox Client for executing queries
            project_id: Project to import labels into
            name: Name of the import job. Can be used to reference the task later
            labels: List of labels
        Returns:
            LabelImport
        """
        data = cls._get_ndjson_from_objects(labels, 'labels')

        if len(labels) > 0 and isinstance(labels[0], Dict):
            label_dicts = cast(List[Dict[str, Any]], labels)
            has_confidence = LabelsConfidencePresenceChecker.check(label_dicts)
            if has_confidence:
                logger.warning("""
                Confidence scores are not supported in Label Import.
                Corresponding confidence score values will be ignored.
                """)
        return cls._create_label_import_from_bytes(client, project_id, name,
                                                   data, len(str(data)))

    @classmethod
    def create_from_url(cls, client: "labelbox.Client", project_id: str,
                        name: str, url: str) -> "LabelImport":
        """
        Create a label annotation import job from a url
        The url must point to a file containing label annotations.

        Args:
            client: Labelbox Client for executing queries
            project_id: Project to import labels into
            name: Name of the import job. Can be used to reference the task later
            url: Url pointing to file to upload
        Returns:
            LabelImport
        """
        if requests.head(url):
            query_str = cls._get_url_mutation()
            return cls(
                client,
                client.execute(query_str,
                               params={
                                   "fileUrl": url,
                                   "projectId": project_id,
                                   'name': name
                               })["createLabelImport"])
        else:
            raise ValueError(f"Url {url} is not reachable")

    @classmethod
    def from_name(cls,
                  client: "labelbox.Client",
                  project_id: str,
                  name: str,
                  as_json: bool = False) -> "LabelImport":
        """
        Retrieves an label import job.

        Args:
            client: Labelbox Client for executing queries
            project_id:  ID used for querying import jobs
            name: Name of the import job.
        Returns:
            LabelImport
        """
        query_str = """query getLabelImportPyApi($projectId : ID!, $name: String!) {
            labelImport(
                where: {projectId: $projectId, name: $name}){
                    %s
                }}""" % query.results_query_part(cls)
        params = {
            "projectId": project_id,
            "name": name,
        }
        response = client.execute(query_str, params)
        if response is None:
            raise labelbox.exceptions.ResourceNotFoundError(LabelImport, params)
        response = response["labelImport"]
        if as_json:
            return response
        return cls(client, response)

    @classmethod
    def _get_url_mutation(cls) -> str:
        return """mutation createLabelImportByUrlPyApi($projectId : ID!, $name: String!, $fileUrl: String!) {
            createLabelImport(data: {
                projectId: $projectId
                name: $name
                fileUrl: $fileUrl
            }) {%s}
        }""" % query.results_query_part(cls)

    @classmethod
    def _get_file_mutation(cls) -> str:
        return """mutation createLabelImportByFilePyApi($projectId : ID!, $name: String!, $file: Upload!, $contentLength: Int!) {
            createLabelImport(data: {
                projectId: $projectId name: $name filePayload: { file: $file, contentLength: $contentLength}
        }) {%s}
        }""" % query.results_query_part(cls)

    @classmethod
    def _create_label_import_from_bytes(cls, client: "labelbox.Client",
                                        project_id: str, name: str,
                                        bytes_data: BinaryIO,
                                        content_len: int) -> "LabelImport":
        file_name = f"{project_id}__{name}.ndjson"
        variables = {
            "file": None,
            "contentLength": content_len,
            "projectId": project_id,
            "name": name
        }
        query_str = cls._get_file_mutation()
        res = cls._create_from_bytes(client, variables, query_str, file_name,
                                     bytes_data)
        return cls(client, res["createLabelImport"])
