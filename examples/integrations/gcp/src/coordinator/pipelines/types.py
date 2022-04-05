from typing import Union, Optional, Dict, Any, Literal
from collections import defaultdict
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum
import os
import time
import uuid
import logging

from google.cloud import storage
from google.cloud import aiplatform
from labelbox.data.serialization import LBV1Converter, NDJsonConverter
from labelbox import ModelRun, Client
from labelbox.data.annotation_types import Radio, Checklist
from labelbox.data.serialization import LBV1Converter, NDJsonConverter
from labelbox.data.metrics.group import get_label_pairs
from labelbox.data.metrics import feature_confusion_matrix_metric
from labelbox import ModelRun
import requests
import ndjson

logger = logging.getLogger("uvicorn")

ClassificationType = Union[Literal['single'], Literal['multi']]


class JobState(Enum):
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'


class PipelineState(Enum):
    EXPORTING_DATA = "EXPORTING_DATA"
    PREPARING_DATA = "PREPARING_DATA"
    TRAINING_MODEL = "TRAINING_MODEL"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


@dataclass
class JobStatus:
    state: JobState
    result: Dict[str, Any] = field(default_factory=dict)
    errors: Optional[str] = None


class Job(ABC):

    def run(self):
        ...


class Pipeline(Job):

    def __init__(self, lb_api_key):
        self.lb_client = Client(lb_api_key, enable_experimental=True)

    def run_job(self, model_run_id, fn):
        try:
            return fn()
        except Exception as e:
            self.update_status(PipelineState.FAILED,
                               model_run_id,
                               error_message=str(e))
            logger.info(f"Job failed. {e}")
            return

    def update_status(self,
                      state: PipelineState,
                      model_run_id,
                      metadata=None,
                      error_message=None):
        model_run = self.lb_client.get_model_run(model_run_id)
        model_run.update_status(state.value, metadata, error_message)

    @abstractmethod
    def parse_args(self, json_data: Dict[str, Any]):
        ...


class InferenceJob(Job):
    # These will eventually be run as an external jobs.
    # Keeping them here for now since the inferences are still run as a separate job
    def __init__(self, lb_api_key: str):
        self.lb_client = Client(lb_api_key)
        self.storage_client = storage.Client(
            project=os.environ['GOOGLE_PROJECT'])

    def parse_uri(self, etl_file):
        parts = etl_file.replace("gs://", "").split("/")
        bucket_name, key = parts[0], "/".join(parts[1:])
        return bucket_name, key

    def get_tool_info(self, model_id):
        # Todo: disambiguate the name. Between the client and the ..
        ontologyId = self.lb_client.execute(
            """query modelOntologyPyApi($modelId: ID!){
                model(where: {id: $modelId}) {ontologyId}}
            """, {'modelId': model_id})['model']['ontologyId']

        ontology = self.lb_client.get_ontology(ontologyId)
        tools = ontology.tools()
        tools = {tool.name: tool.feature_schema_id for tool in tools}
        return tools

    def get_answer_info(self, model_id):
        # Todo: disambiguate the name. Between the client and the ..
        ontologyId = self.lb_client.execute(
            """query modelOntologyPyApi($modelId: ID!){
                model(where: {id: $modelId}) {ontologyId}}
            """, {'modelId': model_id})['model']['ontologyId']

        ontology = self.lb_client.get_ontology(ontologyId)
        tools = ontology.classifications()
        options = {}
        for tool in tools:
            options.update({
                f"{tool.instructions}_{option.value}": {
                    "feature_schema_id": option.feature_schema_id,
                    "parent_feature_schema_id": tool.feature_schema_id,
                    "type": tool.class_type.value
                } for option in tool.options
            })
        return options

    def export_model_run_labels(self, model_run_id,
                                media_type: Union[Literal['image'],
                                                  Literal['text']]):
        query_str = """
            mutation exportModelRunAnnotationsPyApi($modelRunId: ID!) {
                exportModelRunAnnotations(data: {modelRunId: $modelRunId}) {
                    downloadUrl createdAt status
                }
            }
            """
        url = self.lb_client.execute(
            query_str, {'modelRunId': model_run_id},
            experimental=True)['exportModelRunAnnotations']['downloadUrl']
        counter = 1
        while url is None:
            counter += 1
            if counter > 10:
                raise Exception(
                    f"Unsuccessfully got downloadUrl after {counter} attempts.")
            time.sleep(10)
            url = self.lb_client.execute(
                query_str, {'modelRunId': model_run_id},
                experimental=True)['exportModelRunAnnotations']['downloadUrl']

        response = requests.get(url)
        response.raise_for_status()

        contents = ndjson.loads(response.content)
        for row in contents:
            row['media_type'] = media_type
        return LBV1Converter.deserialize(contents)

    def batch_predict(self, etl_file, model, job_name, model_type):

        bucket_name, key = self.parse_uri(etl_file)
        source_uri = self.build_inference_file(bucket_name, key)
        nowgmt = time.strftime("%Y-%m-%d_%H:%M:%S", time.gmtime())
        destination = f"gs://{bucket_name}/inference/{model_type}/{nowgmt}/"
        batch_prediction_job = model.batch_predict(
            job_display_name=job_name,
            instances_format='jsonl',
            machine_type='n1-standard-4',
            gcs_source=[source_uri],
            gcs_destination_prefix=destination,
            sync=False)
        batch_prediction_job.wait_for_resource_creation()
        while batch_prediction_job.state == aiplatform.compat.types.job_state.JobState.JOB_STATE_RUNNING:
            time.sleep(30)
        batch_prediction_job.wait()

        return batch_prediction_job


class ClassificationInferenceJob(InferenceJob):

    def __init__(self, lb_api_key: str, classification_type: ClassificationType,
                 media_type: Union[Literal['image'], Literal['text']]):
        super().__init__(lb_api_key)
        self.classification_threshold = 0.2
        self.media_type = media_type
        self.classification_type = classification_type

    def run(self, etl_file: str, model_run_id: str, model: aiplatform.Model,
            job_name: str):
        batch_prediction_job = self.batch_predict(
            etl_file, model, job_name,
            f"{self.media_type}-{self.classification_type}-classification")
        model_run = self.lb_client._get_single(ModelRun, model_run_id)
        options = self.get_answer_info(model_run.model_id)
        annotation_data = self.process_predictions(batch_prediction_job,
                                                   options)
        predictions = list(NDJsonConverter.deserialize(annotation_data))
        labels = self.export_model_run_labels(model_run_id, 'text')
        self.compute_metrics(labels, predictions, options)
        upload_task = model_run.add_predictions(
            f'diagnostics-import-{uuid.uuid4()}',
            NDJsonConverter.serialize(predictions))
        upload_task.wait_until_done()
        logger.info(
            f"IMPORT ERRORS : {upload_task.errors}. Imported {len(predictions)}"
        )
        return JobStatus(JobState.SUCCESS)

    def process_predictions(self, batch_prediction_job, options):
        annotation_data = []
        for batch in batch_prediction_job.iter_outputs():
            for prediction_data in ndjson.loads(batch.download_as_string()):
                if 'error' in prediction_data:
                    logger.info(f"Row failed. {prediction_data}")
                    continue
                prediction = prediction_data['prediction']

                # only way to get data row id is to lookup from the content uri
                data_row_id = prediction_data['instance']['content'].split(
                    "/")[-1].replace(
                        ".txt" if self.media_type == "text" else ".jpg", "")

                if self.classification_type == 'single':
                    annotation_data.append(
                        self.build_upload_data_single(prediction, options,
                                                      data_row_id))
                else:
                    annotation_data.extend(
                        self.build_upload_data_multi(prediction, options,
                                                     data_row_id))
        return annotation_data

    def compute_metrics(self, labels, predictions, options):
        pairs = get_label_pairs(labels, predictions, filter_mismatch=True)
        for (ground_truth, prediction) in pairs.values():
            for annotation in prediction.annotations:
                self.add_name_to_annotation(annotation, options)

            for annotation in ground_truth.annotations:
                self.add_name_to_annotation(annotation, options)

            prediction.annotations.extend(
                feature_confusion_matrix_metric(ground_truth.annotations,
                                                prediction.annotations))

    def add_name_to_annotation(self, annotation, options):
        tool_name_lookup = {
            v['feature_schema_id']: k for k, v in options.items()
        }
        annotation.name = " "
        if isinstance(annotation.value, Radio):
            annotation.value.answer.name = tool_name_lookup[
                annotation.value.answer.feature_schema_id].replace(' ', '-')
        elif isinstance(annotation.value, Checklist):
            for answer in annotation.value.answer:
                answer.name = tool_name_lookup[
                    answer.feature_schema_id].replace(' ', '-')

    def build_upload_data_single(self, prediction, options, data_row_id):
        confidences = prediction['confidences']
        argmax = confidences.index(max(confidences))
        predicted = prediction['displayNames'][argmax]
        return {
            "uuid": str(uuid.uuid4()),
            "answer": {
                'schemaId': options[predicted]['feature_schema_id']
            },
            'dataRow': {
                "id": data_row_id
            },
            "schemaId": options[predicted]['parent_feature_schema_id']
        }

    def build_upload_data_multi(self, prediction, options, data_row_id):
        names = prediction['displayNames']
        scores = prediction['confidences']
        answers = defaultdict(list)

        for name, score in zip(names, scores):
            if score > self.classification_threshold:
                # We need to know the parent id type.
                # E.g. they could be uploading to multiple radios...
                # OR they could be uploading to one dropdown...
                tool = options[name]
                tool_type = tool['type']
                answers[(tool_type, tool['parent_feature_schema_id'])].append(
                    {'schemaId': options[name]['feature_schema_id']})

        if len(answers):
            for (tool_type, parent_schema_id), answer_list in answers.items():
                if tool_type == 'radio':
                    for answer in answer_list:
                        yield {
                            "uuid": str(uuid.uuid4()),
                            'answer': answer,
                            'dataRow': {
                                "id": data_row_id
                            },
                            "schemaId": parent_schema_id
                        }
                elif tool_type == 'checklist':
                    yield {
                        "uuid": str(uuid.uuid4()),
                        'answer': answer_list,
                        'dataRow': {
                            "id": data_row_id
                        },
                        "schemaId": parent_schema_id
                    }
                else:
                    raise ValueError("Only radio and checklists are supported")

    def build_inference_file(self, bucket_name, key):
        bucket = self.storage_client.get_bucket(bucket_name)
        # Create a blob object from the filepath
        blob = bucket.blob(key)
        contents = ndjson.loads(blob.download_as_string())
        prediction_inputs = []
        content_key = "textGcsUri" if self.media_type == 'text' else "imageGcsUri"
        mimetype = "text/plain" if self.media_type == 'text' else "image/jpeg"
        for line in contents:
            prediction_inputs.append({
                "content": line[content_key],
                "mimeType": mimetype
            })

        nowgmt = time.strftime("%Y-%m-%d_%H:%M:%S", time.gmtime())
        blob = bucket.blob(
            f"inference_file/{self.media_type}-{self.classification_type}-classification/{nowgmt}.jsonl"
        )
        blob.upload_from_string(data=ndjson.dumps(prediction_inputs),
                                content_type="application/jsonl")
        return f"gs://{bucket.name}/{blob.name}"
