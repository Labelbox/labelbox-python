from typing import TYPE_CHECKING, Dict, Iterable, Union, List, Optional, Any
from pathlib import Path
import os
import time
import logging
import requests
import ndjson

from labelbox.pagination import PaginatedCollection
from labelbox.orm.query import results_query_part
from labelbox.orm.model import Field, Relationship, Entity
from labelbox.orm.db_object import DbObject, experimental

if TYPE_CHECKING:
    from labelbox import MEAPredictionImport

logger = logging.getLogger(__name__)


class ModelRun(DbObject):
    name = Field.String("name")
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    created_by_id = Field.String("created_by_id", "createdBy")
    model_id = Field.String("model_id")

    def upsert_labels(self, label_ids, timeout_seconds=60):
        """ Adds data rows and labels to a model run
        Args:
            label_ids (list): label ids to insert
            timeout_seconds (float): Max waiting time, in seconds.
        Returns:
            ID of newly generated async task
        """

        if len(label_ids) < 1:
            raise ValueError("Must provide at least one label id")

        mutation_name = 'createMEAModelRunLabelRegistrationTask'
        create_task_query_str = """mutation createMEAModelRunLabelRegistrationTaskPyApi($modelRunId: ID!, $labelIds : [ID!]!) {
          %s(where : { id : $modelRunId}, data : {labelIds: $labelIds})}
          """ % (mutation_name)

        res = self.client.execute(create_task_query_str, {
            'modelRunId': self.uid,
            'labelIds': label_ids
        })
        task_id = res[mutation_name]

        status_query_str = """query MEALabelRegistrationTaskStatusPyApi($where: WhereUniqueIdInput!){
            MEALabelRegistrationTaskStatus(where: $where) {status errorMessage}
        }
        """
        return self._wait_until_done(lambda: self.client.execute(
            status_query_str, {'where': {
                'id': task_id
            }})['MEALabelRegistrationTaskStatus'],
                                     timeout_seconds=timeout_seconds)

    def upsert_data_rows(self, data_row_ids, timeout_seconds=60):
        """ Adds data rows to a model run without any associated labels
        Args:
            data_row_ids (list): data row ids to add to mea
            timeout_seconds (float): Max waiting time, in seconds.
        Returns:
            ID of newly generated async task
        """

        if len(data_row_ids) < 1:
            raise ValueError("Must provide at least one data row id")

        mutation_name = 'createMEAModelRunDataRowRegistrationTask'
        create_task_query_str = """mutation createMEAModelRunDataRowRegistrationTaskPyApi($modelRunId: ID!, $dataRowIds : [ID!]!) {
          %s(where : { id : $modelRunId}, data : {dataRowIds: $dataRowIds})}
          """ % (mutation_name)

        res = self.client.execute(create_task_query_str, {
            'modelRunId': self.uid,
            'dataRowIds': data_row_ids
        })
        task_id = res[mutation_name]

        status_query_str = """query MEADataRowRegistrationTaskStatusPyApi($where: WhereUniqueIdInput!){
            MEADataRowRegistrationTaskStatus(where: $where) {status errorMessage}
        }
        """
        return self._wait_until_done(lambda: self.client.execute(
            status_query_str, {'where': {
                'id': task_id
            }})['MEADataRowRegistrationTaskStatus'],
                                     timeout_seconds=timeout_seconds)

    def _wait_until_done(self, status_fn, timeout_seconds=60, sleep_time=5):
        # Do not use this function outside of the scope of upsert_data_rows or upsert_labels. It could change.
        while True:
            res = status_fn()
            if res['status'] == 'COMPLETE':
                return True
            elif res['status'] == 'FAILED':
                raise Exception(
                    f"MEA Import Failed. Details : {res['errorMessage']}")
            timeout_seconds -= sleep_time
            if timeout_seconds <= 0:
                raise TimeoutError(
                    f"Unable to complete import within {timeout_seconds} seconds."
                )

            time.sleep(sleep_time)

    def add_predictions(
        self,
        name: str,
        predictions: Union[str, Path, Iterable[Dict]],
    ) -> 'MEAPredictionImport':  # type: ignore
        """ Uploads predictions to a new Editor project.
        Args:
            name (str): name of the AnnotationImport job
            predictions (str or Path or Iterable):
                url that is publicly accessible by Labelbox containing an
                ndjson file
                OR local path to an ndjson file
                OR iterable of annotation rows
        Returns:
            AnnotationImport
        """
        kwargs = dict(client=self.client, model_run_id=self.uid, name=name)
        if isinstance(predictions, str) or isinstance(predictions, Path):
            if os.path.exists(predictions):
                return Entity.MEAPredictionImport.create_from_file(
                    path=str(predictions), **kwargs)
            else:
                return Entity.MEAPredictionImport.create_from_url(
                    url=str(predictions), **kwargs)
        elif isinstance(predictions, Iterable):
            return Entity.MEAPredictionImport.create_from_objects(
                predictions=predictions, **kwargs)
        else:
            raise ValueError(
                f'Invalid predictions given of type: {type(predictions)}')

    def model_run_data_rows(self):
        query_str = """query modelRunPyApi($modelRunId: ID!, $from : String, $first: Int){
                annotationGroups(where: {modelRunId: {id: $modelRunId}}, after: $from, first: $first)
                {nodes{%s},pageInfo{endCursor}}
            }
        """ % (results_query_part(ModelRunDataRow))
        return PaginatedCollection(
            self.client, query_str, {'modelRunId': self.uid},
            ['annotationGroups', 'nodes'],
            lambda client, res: ModelRunDataRow(client, self.model_id, res),
            ['annotationGroups', 'pageInfo', 'endCursor'])

    def delete(self):
        """ Deletes specified model run.

        Returns:
            Query execution success.
        """
        ids_param = "ids"
        query_str = """mutation DeleteModelRunPyApi($%s: ID!) {
            deleteModelRuns(where: {ids: [$%s]})}""" % (ids_param, ids_param)
        self.client.execute(query_str, {ids_param: str(self.uid)})

    def delete_model_run_data_rows(self, data_row_ids):
        """ Deletes data rows from model runs.

        Args:
            data_row_ids (list): List of data row ids to delete from the model run.
        Returns:
            Query execution success.
        """
        model_run_id_param = "modelRunId"
        data_row_ids_param = "dataRowIds"
        query_str = """mutation DeleteModelRunDataRowsPyApi($%s: ID!, $%s: [ID!]!) {
            deleteModelRunDataRows(where: {modelRunId: $%s, dataRowIds: $%s})}""" % (
            model_run_id_param, data_row_ids_param, model_run_id_param,
            data_row_ids_param)
        self.client.execute(query_str, {
            model_run_id_param: self.uid,
            data_row_ids_param: data_row_ids
        })

    @experimental
    def update_status(self,
                      status: str,
                      metadata: Optional[Dict[str, str]] = None,
                      error_message: Optional[str] = None):

        valid_statuses = [
            "EXPORTING_DATA", "PREPARING_DATA", "TRAINING_MODEL", "COMPLETE",
            "FAILED"
        ]
        if status not in valid_statuses:
            raise ValueError(
                f"Status must be one of : `{valid_statuses}`. Found : `{status}`"
            )

        data: Dict[str, Any] = {'status': status}
        if error_message:
            data['errorMessage'] = error_message

        if metadata:
            data['metadata'] = metadata

        self.client.execute(
            """mutation setPipelineStatusPyApi($modelRunId: ID!, $data: UpdateTrainingPipelineInput!){
                updateTrainingPipeline(modelRun: {id : $modelRunId}, data: $data){status}
            }
        """, {
                'modelRunId': self.uid,
                'data': data
            },
            experimental=True)

    @experimental
    def export_labels(
        self,
        download: bool = False,
        timeout_seconds: int = 600
    ) -> Optional[Union[str, List[Dict[Any, Any]]]]:
        """
        Experimental. To use, make sure client has enable_experimental=True.

        Fetches Labels from the ModelRun

        Args:
            download (bool): Returns the url if False
        Returns:
            URL of the data file with this ModelRun's labels.
            If download=True, this instead returns the contents as NDJSON format.
            If the server didn't generate during the `timeout_seconds` period,
            None is returned.
        """
        sleep_time = 2
        query_str = """mutation exportModelRunAnnotationsPyApi($modelRunId: ID!) {
                exportModelRunAnnotations(data: {modelRunId: $modelRunId}) {
                    downloadUrl createdAt status
                }
            }
            """

        while True:
            url = self.client.execute(
                query_str, {'modelRunId': self.uid},
                experimental=True)['exportModelRunAnnotations']['downloadUrl']

            if url:
                if not download:
                    return url
                else:
                    response = requests.get(url)
                    response.raise_for_status()
                    return ndjson.loads(response.content)

            timeout_seconds -= sleep_time
            if timeout_seconds <= 0:
                return None

            logger.debug("ModelRun '%s' label export, waiting for server...",
                         self.uid)
            time.sleep(sleep_time)


class ModelRunDataRow(DbObject):
    label_id = Field.String("label_id")
    model_run_id = Field.String("model_run_id")
    data_row = Relationship.ToOne("DataRow", False, cache=True)

    def __init__(self, client, model_id, *args, **kwargs):
        super().__init__(client, *args, **kwargs)
        self.model_id = model_id

    @property
    def url(self):
        app_url = self.client.app_url
        endpoint = f"{app_url}/models/{self.model_id}/{self.model_run_id}/AllDatarowsSlice/{self.uid}?view=carousel"
        return endpoint
