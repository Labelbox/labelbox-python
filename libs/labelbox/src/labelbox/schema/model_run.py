# type: ignore
import logging
import os
import time
import warnings
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Iterable, Union, Tuple, List, Optional, Any

import requests

from labelbox import parser
from labelbox.orm.db_object import DbObject, experimental
from labelbox.orm.model import Field, Relationship, Entity
from labelbox.orm.query import results_query_part
from labelbox.pagination import PaginatedCollection
from labelbox.schema.conflict_resolution_strategy import ConflictResolutionStrategy
from labelbox.schema.export_params import ModelRunExportParams
from labelbox.schema.export_task import ExportTask
from labelbox.schema.identifiables import UniqueIds, GlobalKeys, DataRowIds
from labelbox.schema.send_to_annotate_params import SendToAnnotateFromModelParams, build_destination_task_queue_input, \
    build_predictions_input
from labelbox.schema.task import Task

if TYPE_CHECKING:
    from labelbox import MEAPredictionImport
    from labelbox.types import Label

logger = logging.getLogger(__name__)

DATAROWS_IMPORT_LIMIT = 25000


class DataSplit(Enum):
    TRAINING = "TRAINING"
    TEST = "TEST"
    VALIDATION = "VALIDATION"
    UNASSIGNED = "UNASSIGNED"


class ModelRun(DbObject):
    name = Field.String("name")
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    created_by_id = Field.String("created_by_id", "createdBy")
    model_id = Field.String("model_id")
    training_metadata = Field.Json("training_metadata")

    class Status(Enum):
        EXPORTING_DATA = "EXPORTING_DATA"
        PREPARING_DATA = "PREPARING_DATA"
        TRAINING_MODEL = "TRAINING_MODEL"
        COMPLETE = "COMPLETE"
        FAILED = "FAILED"

    def upsert_labels(self,
                      label_ids: Optional[List[str]] = None,
                      project_id: Optional[str] = None,
                      timeout_seconds=3600):
        """
        Adds data rows and labels to a Model Run

        Args:
            label_ids (list): label ids to insert
            project_id (string): project uuid, all project labels will be uploaded
                Either label_ids OR project_id is required but NOT both
            timeout_seconds (float): Max waiting time, in seconds.
        Returns:
            ID of newly generated async task

        """

        use_label_ids = label_ids is not None and len(label_ids) > 0
        use_project_id = project_id is not None

        if not use_label_ids and not use_project_id:
            raise ValueError(
                "Must provide at least one label id or a project id")

        if use_label_ids and use_project_id:
            raise ValueError("Must only one of label ids, project id")

        if use_label_ids:
            return self._upsert_labels_by_label_ids(label_ids, timeout_seconds)
        else:  # use_project_id
            return self._upsert_labels_by_project_id(project_id,
                                                     timeout_seconds)

    def _upsert_labels_by_label_ids(self, label_ids: List[str],
                                    timeout_seconds: int):
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

    def _upsert_labels_by_project_id(self, project_id: str,
                                     timeout_seconds: int):
        mutation_name = 'createMEAModelRunProjectLabelRegistrationTask'
        create_task_query_str = """mutation createMEAModelRunProjectLabelRegistrationTaskPyApi($modelRunId: ID!, $projectId : ID!) {
        %s(where : { modelRunId : $modelRunId, projectId: $projectId})}
        """ % (mutation_name)

        res = self.client.execute(create_task_query_str, {
            'modelRunId': self.uid,
            'projectId': project_id
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

    def upsert_data_rows(self,
                         data_row_ids=None,
                         global_keys=None,
                         timeout_seconds=3600):
        """ Adds data rows to a Model Run without any associated labels
        Args:
            data_row_ids (list): data row ids to add to model run
            global_keys (list): global keys for data rows to add to model run
            timeout_seconds (float): Max waiting time, in seconds.
        Returns:
            ID of newly generated async task
        """

        mutation_name = 'createMEAModelRunDataRowRegistrationTask'
        create_task_query_str = """mutation createMEAModelRunDataRowRegistrationTaskPyApi($modelRunId: ID!, $dataRowIds: [ID!], $globalKeys: [ID!]) {
          %s(where : { id : $modelRunId}, data : {dataRowIds: $dataRowIds, globalKeys: $globalKeys})}
          """ % (mutation_name)

        res = self.client.execute(
            create_task_query_str, {
                'modelRunId': self.uid,
                'dataRowIds': data_row_ids,
                'globalKeys': global_keys
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

    def _wait_until_done(self, status_fn, timeout_seconds=120, sleep_time=5):
        # Do not use this function outside of the scope of upsert_data_rows or upsert_labels. It could change.
        original_timeout = timeout_seconds
        while True:
            res = status_fn()
            if res['status'] == 'COMPLETE':
                return True
            elif res['status'] == 'FAILED':
                raise Exception(f"Job failed.")
            timeout_seconds -= sleep_time
            if timeout_seconds <= 0:
                raise TimeoutError(
                    f"Unable to complete import within {original_timeout} seconds."
                )
            time.sleep(sleep_time)

    def upsert_predictions_and_send_to_project(
        self,
        name: str,
        predictions: Union[str, Path, Iterable[Dict]],
        project_id: str,
        priority: Optional[int] = 5,
    ) -> 'MEAPredictionImport':  # type: ignore
        """
        Provides a convenient way to execute the following steps in a single function call:
            1. Upload predictions to a Model
            2. Create a batch from data rows that had predictions assocated with them
            3. Attach the batch to a project
            4. Add those same predictions to the project as MAL annotations

        Note that partial successes are possible.
        If it is important that all stages are successful then check the status of each individual task
        with task.errors. E.g.

        >>>    mea_import_job, batch, mal_import_job = upsert_predictions_and_send_to_project(name, predictions, project_id)
        >>>    # handle mea import job successfully created (check for job failure or partial failures)
        >>>    print(mea_import_job.status, mea_import_job.errors)
        >>>    if batch is None:
        >>>        # Handle batch creation failure
        >>>    if mal_import_job is None:
        >>>        # Handle mal_import_job creation failure
        >>>    else:
        >>>        # handle mal import job successfully created (check for job failure or partial failures)
        >>>        print(mal_import_job.status, mal_import_job.errors)


        Args:
            name (str): name of the AnnotationImport job as well as the name of the batch import
            predictions (Iterable):
                iterable of annotation rows
            project_id (str): id of the project to import into
            priority (int): priority of the job
        Returns:
            Tuple[MEAPredictionImport, Batch, MEAToMALPredictionImport]
            If any of these steps fail the return value will be None.

        """
        kwargs = dict(client=self.client, model_run_id=self.uid, name=name)
        project = self.client.get_project(project_id)
        import_job = self.add_predictions(name, predictions)
        prediction_statuses = import_job.statuses
        mea_to_mal_data_rows = list(
            set([
                row['dataRow']['id']
                for row in prediction_statuses
                if row['status'] == 'SUCCESS'
            ]))

        if not mea_to_mal_data_rows:
            # 0 successful model predictions imported
            return import_job, None, None

        elif len(mea_to_mal_data_rows) >= DATAROWS_IMPORT_LIMIT:
            mea_to_mal_data_rows = mea_to_mal_data_rows[:DATAROWS_IMPORT_LIMIT]
            logger.warning(
                f"Exeeded max data row limit {len(mea_to_mal_data_rows)}, trimmed down to {DATAROWS_IMPORT_LIMIT} data rows."
            )

        try:
            batch = project.create_batch(name, mea_to_mal_data_rows, priority)
        except Exception as e:
            logger.warning(f"Failed to create batch. Messsage : {e}.")
            # Unable to create batch
            return import_job, None, None

        try:
            mal_prediction_import = Entity.MEAToMALPredictionImport.create_for_model_run_data_rows(
                data_row_ids=mea_to_mal_data_rows,
                project_id=project_id,
                **kwargs)
            mal_prediction_import.wait_until_done()
        except Exception as e:
            logger.warning(
                f"Failed to create MEA to MAL prediction import. Message : {e}."
            )
            # Unable to create mea to mal prediction import
            return import_job, batch, None

        return import_job, batch, mal_prediction_import

    def add_predictions(
        self,
        name: str,
        predictions: Union[str, Path, Iterable[Dict], Iterable["Label"]],
    ) -> 'MEAPredictionImport':  # type: ignore
        """
        Uploads predictions to a new Editor project.

        Args:
            name (str): name of the AnnotationImport job
            predictions (str or Path or Iterable): url that is publicly accessible by Labelbox containing an
                ndjson file
                OR local path to an ndjson file
                OR iterable of annotation rows

        Returns:
            AnnotationImport
        """
        kwargs = dict(client=self.client, id=self.uid, name=name)
        if isinstance(predictions, str) or isinstance(predictions, Path):
            if os.path.exists(predictions):
                return Entity.MEAPredictionImport.create(path=str(predictions),
                                                         **kwargs)
            else:
                return Entity.MEAPredictionImport.create(url=str(predictions),
                                                         **kwargs)
        elif isinstance(predictions, Iterable):
            return Entity.MEAPredictionImport.create(labels=predictions,
                                                     **kwargs)
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
        """ Deletes specified Model Run.

        Returns:
            Query execution success.
        """
        ids_param = "ids"
        query_str = """mutation DeleteModelRunPyApi($%s: ID!) {
            deleteModelRuns(where: {ids: [$%s]})}""" % (ids_param, ids_param)
        self.client.execute(query_str, {ids_param: str(self.uid)})

    def delete_model_run_data_rows(self, data_row_ids: List[str]):
        """ Deletes data rows from Model Runs.

        Args:
            data_row_ids (list): List of data row ids to delete from the Model Run.
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
    def assign_data_rows_to_split(self,
                                  data_row_ids: List[str] = None,
                                  split: Union[DataSplit, str] = None,
                                  global_keys: List[str] = None,
                                  timeout_seconds=120):

        split_value = split.value if isinstance(split, DataSplit) else split
        valid_splits = DataSplit._member_names_

        if split_value is None or split_value not in valid_splits:
            raise ValueError(
                f"`split` must be one of : `{valid_splits}`. Found : `{split}`")

        task_id = self.client.execute(
            """mutation assignDataSplitPyApi($modelRunId: ID!, $data: CreateAssignDataRowsToDataSplitTaskInput!){
                  createAssignDataRowsToDataSplitTask(modelRun : {id: $modelRunId}, data: $data)}
            """, {
                'modelRunId': self.uid,
                'data': {
                    'assignments': [{
                        'split': split_value,
                        'dataRowIds': data_row_ids,
                        'globalKeys': global_keys,
                    }]
                }
            },
            experimental=True)['createAssignDataRowsToDataSplitTask']

        status_query_str = """query assignDataRowsToDataSplitTaskStatusPyApi($id: ID!){
            assignDataRowsToDataSplitTaskStatus(where: {id : $id}){status errorMessage}}
            """

        return self._wait_until_done(lambda: self.client.execute(
            status_query_str, {'id': task_id}, experimental=True)[
                'assignDataRowsToDataSplitTaskStatus'],
                                     timeout_seconds=timeout_seconds)

    @experimental
    def update_status(self,
                      status: Union[str, "ModelRun.Status"],
                      metadata: Optional[Dict[str, str]] = None,
                      error_message: Optional[str] = None):

        status_value = status.value if isinstance(status,
                                                  ModelRun.Status) else status
        if status_value not in ModelRun.Status._member_names_:
            raise ValueError(
                f"Status must be one of : `{ModelRun.Status._member_names_}`. Found : `{status_value}`"
            )

        data: Dict[str, Any] = {'status': status_value}
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
    def update_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
         Updates the Model Run's training metadata config
         Args:
             config (dict): A dictionary of keys and values
         Returns:
             Model Run id and updated training metadata
         """
        data: Dict[str, Any] = {'config': config}
        res = self.client.execute(
            """mutation updateModelRunConfigPyApi($modelRunId: ID!, $data: UpdateModelRunConfigInput!){
                updateModelRunConfig(modelRun: {id : $modelRunId}, data: $data){trainingMetadata}
            }
        """, {
                'modelRunId': self.uid,
                'data': data
            },
            experimental=True)
        return res["updateModelRunConfig"]

    @experimental
    def reset_config(self) -> Dict[str, Any]:
        """
         Resets Model Run's training metadata config
         Returns:
             Model Run id and reset training metadata
         """
        res = self.client.execute(
            """mutation resetModelRunConfigPyApi($modelRunId: ID!){
                resetModelRunConfig(modelRun: {id : $modelRunId}){trainingMetadata}
            }
        """, {'modelRunId': self.uid},
            experimental=True)
        return res["resetModelRunConfig"]

    @experimental
    def get_config(self) -> Dict[str, Any]:
        """
         Gets Model Run's training metadata
         Returns:
             training metadata as a dictionary
         """
        res = self.client.execute("""query ModelRunPyApi($modelRunId: ID!){
                modelRun(where: {id : $modelRunId}){trainingMetadata}
            }
        """, {'modelRunId': self.uid},
                                  experimental=True)
        return res["modelRun"]["trainingMetadata"]

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
        warnings.warn(
            "You are currently utilizing exports v1 for this action, which will be deprecated after April 30th, 2024. We recommend transitioning to exports v2. To view export v2 details, visit our docs: https://docs.labelbox.com/reference/label-export",
            DeprecationWarning)
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
                    return parser.loads(response.content)

            timeout_seconds -= sleep_time
            if timeout_seconds <= 0:
                return None

            logger.debug("ModelRun '%s' label export, waiting for server...",
                         self.uid)
            time.sleep(sleep_time)

    def export(self,
               task_name: Optional[str] = None,
               params: Optional[ModelRunExportParams] = None) -> ExportTask:
        """
        Creates a model run export task with the given params and returns the task.

        >>>    export_task = export("my_export_task", params={"media_attributes": True})

        """
        task, _ = self._export(task_name, params, streamable=True)
        return ExportTask(task)

    def export_v2(
        self,
        task_name: Optional[str] = None,
        params: Optional[ModelRunExportParams] = None,
    ) -> Union[Task, ExportTask]:
        """
        Creates a model run export task with the given params and returns the task.

        >>>    export_task = export_v2("my_export_task", params={"media_attributes": True})

        """
        task, is_streamable = self._export(task_name, params)
        if (is_streamable):
            return ExportTask(task, True)
        return task

    def _export(
        self,
        task_name: Optional[str] = None,
        params: Optional[ModelRunExportParams] = None,
        streamable: bool = False,
    ) -> Tuple[Task, bool]:
        mutation_name = "exportDataRowsInModelRun"
        create_task_query_str = (
            f"mutation {mutation_name}PyApi"
            f"($input: ExportDataRowsInModelRunInput!)"
            f"{{{mutation_name}(input: $input){{taskId isStreamable}}}}")

        _params = params or ModelRunExportParams()

        query_params = {
            "input": {
                "taskName": task_name,
                "filters": {
                    "modelRunId": self.uid
                },
                "isStreamableReady": True,
                "params": {
                    "mediaTypeOverride":
                        _params.get('media_type_override', None),
                    "includeAttachments":
                        _params.get('attachments', False),
                    "includeEmbeddings":
                        _params.get('embeddings', False),
                    "includeMetadata":
                        _params.get('metadata_fields', False),
                    "includeDataRowDetails":
                        _params.get('data_row_details', False),
                    "includePredictions":
                        _params.get('predictions', False),
                    "includeModelRunDetails":
                        _params.get('model_run_details', False),
                },
                "streamable": streamable
            }
        }
        res = self.client.execute(create_task_query_str,
                                  query_params,
                                  error_log_key="errors")
        res = res[mutation_name]
        task_id = res["taskId"]
        is_streamable = res["isStreamable"]
        return Task.get_task(self.client, task_id), is_streamable

    def send_to_annotate_from_model(
            self, destination_project_id: str, task_queue_id: Optional[str],
            batch_name: str, data_rows: Union[DataRowIds, GlobalKeys],
            params: SendToAnnotateFromModelParams) -> Task:
        """
        Sends data rows from a model run to a project for annotation.

        Example Usage:
            >>> task = model_run.send_to_annotate_from_model(
            >>>     destination_project_id=DESTINATION_PROJECT_ID,
            >>>     batch_name="batch",
            >>>     data_rows=UniqueIds([DATA_ROW_ID]),
            >>>     task_queue_id=TASK_QUEUE_ID,
            >>>     params={})
            >>> task.wait_till_done()

        Args:
            destination_project_id: The ID of the project to send the data rows to.
            task_queue_id: The ID of the task queue to send the data rows to.  If not specified, the data rows will be
                sent to the Done workflow state.
            batch_name: The name of the batch to create. If more than one batch is created, additional batches will be
                named with a monotonically increasing numerical suffix, starting at "_1".
            data_rows: The data rows to send to the project.
            params: Additional parameters for this operation. See SendToAnnotateFromModelParams for details.

        Returns: The created task for this operation.

        """

        mutation_str = """mutation SendToAnnotateFromMeaPyApi($input: SendToAnnotateFromMeaInput!) {
                            sendToAnnotateFromMea(input: $input) {
                              taskId
                            }
                          }
        """

        destination_task_queue = build_destination_task_queue_input(
            task_queue_id)
        data_rows_query = self.client.build_catalog_query(data_rows)

        predictions_ontology_mapping = params.get(
            "predictions_ontology_mapping", None)
        predictions_input = build_predictions_input(
            predictions_ontology_mapping, self.uid)

        batch_priority = params.get("batch_priority", 5)
        exclude_data_rows_in_project = params.get(
            "exclude_data_rows_in_project", False)
        override_existing_annotations_rule = params.get(
            "override_existing_annotations_rule",
            ConflictResolutionStrategy.KeepExisting)
        res = self.client.execute(
            mutation_str, {
                "input": {
                    "destinationProjectId":
                        destination_project_id,
                    "batchInput": {
                        "batchName": batch_name,
                        "batchPriority": batch_priority
                    },
                    "destinationTaskQueue":
                        destination_task_queue,
                    "excludeDataRowsInProject":
                        exclude_data_rows_in_project,
                    "annotationsInput":
                        None,
                    "predictionsInput":
                        predictions_input,
                    "conflictLabelsResolutionStrategy":
                        override_existing_annotations_rule,
                    "searchQuery": [data_rows_query],
                    "sourceModelRunId":
                        self.uid
                }
            })['sendToAnnotateFromMea']

        return Entity.Task.get_task(self.client, res['taskId'])


class ModelRunDataRow(DbObject):
    label_id = Field.String("label_id")
    model_run_id = Field.String("model_run_id")
    data_split = Field.Enum(DataSplit, "data_split")
    data_row = Relationship.ToOne("DataRow", False, cache=True)

    def __init__(self, client, model_id, *args, **kwargs):
        super().__init__(client, *args, **kwargs)
        self.model_id = model_id

    @property
    def url(self):
        app_url = self.client.app_url
        endpoint = f"{app_url}/models/{self.model_id}/{self.model_run_id}/AllDatarowsSlice/{self.uid}?view=carousel"
        return endpoint
