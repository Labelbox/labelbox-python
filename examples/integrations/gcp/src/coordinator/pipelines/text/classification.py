from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Union, Literal
import time
import os
import logging
import uuid
from collections import defaultdict
import requests

from google.cloud import aiplatform
from google.cloud import storage
from google.cloud.aiplatform import Model
from labelbox import Client, ModelRun
from labelbox.data.serialization import LBV1Converter, NDJsonConverter
from labelbox.data.metrics.group import get_label_pairs
from labelbox.data.metrics import feature_confusion_matrix_metric
from labelbox.data.annotation_types import Checklist, Radio

from pipelines.types import Pipeline, JobStatus, JobState, Job

logger = logging.getLogger("uvicorn")

TextClassificationType = Union[Literal['single'], Literal['multi']]

#import time
from google.cloud import aiplatform
#import os
#import json
import ndjson
#from io import BytesIO


class TextClassificationETL(Job):

    def __init__(self, classification_type: TextClassificationType,
                 gcs_bucket: str, service_account_email: str,
                 google_cloud_project: str):
        self.classification_type = classification_type
        self.gcs_bucket = gcs_bucket
        self.service_account_email = service_account_email
        self.google_cloud_project = google_cloud_project
        self.container_name = f"gcr.io/{google_cloud_project}/training-repo/text_classification_etl"

    def run(self, model_run_id: str, job_name) -> JobStatus:
        nowgmt = time.strftime("%Y-%m-%d_%H:%M:%S", time.gmtime())
        gcs_key = f'etl/text-{self.classification_type}-classification/{nowgmt}.jsonl'
        CMDARGS = [
            f"--gcs_bucket={self.gcs_bucket}", f"--model_run_id={model_run_id}",
            f"--gcs_key={gcs_key}",
            f"--classification_type={self.classification_type}"
        ]
        job = aiplatform.CustomContainerTrainingJob(
            display_name=job_name,
            container_uri=self.container_name,
        )
        job.run(
            args=CMDARGS,
            service_account=self.service_account_email,
            environment_variables={'GOOGLE_PROJECT': self.google_cloud_project})
        return JobStatus(JobState.SUCCESS,
                         result=f'gs://{self.gcs_bucket}/{gcs_key}')


class TextClassificationTraining(Job):

    def __init__(self, classification_type: TextClassificationType):
        self.classification_type = classification_type
        if classification_type == 'single':
            self.multi_label = False
            self.import_schema_uri = aiplatform.schema.dataset.ioformat.text.single_label_classification
        elif classification_type == 'multi':
            self.multi_label = True
            self.import_schema_uri = aiplatform.schema.dataset.ioformat.text.multi_label_classification
        else:
            raise ValueError(
                f"Unexpected classification type: `{classification_type}`")

    def run(self, training_file_uri: str, job_name: str) -> JobStatus:
        dataset = aiplatform.TextDataset.create(
            display_name=job_name,
            gcs_source=[training_file_uri],
            import_schema_uri=self.import_schema_uri)
        job = aiplatform.AutoMLTextTrainingJob(
            display_name=job_name,
            prediction_type="classification",
            multi_label=self.multi_label,
        )
        model = job.run(
            dataset=dataset,
            training_filter_split=
            "labels.aiplatform.googleapis.com/ml_use=training",
            validation_filter_split=
            "labels.aiplatform.googleapis.com/ml_use=validation",
            test_filter_split="labels.aiplatform.googleapis.com/ml_use=test")
        logger.info("model id: %s" % model.name)
        return JobStatus(JobState.SUCCESS,
                         result={
                             'model_id': model.name,
                             'model': model
                         })


class TextClassificationDeployment(Job):

    def run(self, model: Model, job_name: str) -> JobStatus:
        endpoint = model.deploy(deployed_model_display_name=job_name)
        return JobStatus(JobState.SUCCESS,
                         result={'endpoint_id': endpoint.name})


class TextClassificationInference(Job):

    def __init__(self, labelbox_api_key: str,
                 classification_type: TextClassificationType):
        # This will eventually be run as an external job.
        # Keeping it here for now since the inferences are still run as a separate job
        self.classification_type = classification_type
        self.classification_threshold = 0.2
        self.lb_client = Client(labelbox_api_key)
        self.storage_client = storage.Client(
            project=os.environ['GOOGLE_PROJECT'])

    def parse_uri(self, etl_file):
        parts = etl_file.replace("gs://", "").split("/")
        bucket_name, key = parts[0], "/".join(parts[1:])
        return bucket_name, key

    def build_inference_file(self, bucket_name, key):
        bucket = self.storage_client.get_bucket(bucket_name)
        # Create a blob object from the filepath
        blob = bucket.blob(key)
        contents = ndjson.loads(blob.download_as_string())
        stuff = {}
        for line in contents:
            stuff[line['dataItemResourceLabels']['dataRowId']] = {
                "content": line['textGcsUri'],
                "mimeType": "text/plain"
            }

        nowgmt = time.strftime("%Y-%m-%d_%H:%M:%S", time.gmtime())
        blob = bucket.blob(
            f"inference_file/text-{self.classification_type}-classification/{nowgmt}.jsonl"
        )
        blob.upload_from_string(data=ndjson.dumps(list(stuff.values())),
                                content_type="application/jsonl")
        return f"gs://{bucket.name}/{blob.name}"

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
                answers[options[name]['parent_feature_schema_id']].append(
                    {'schemaId': options[name]['feature_schema_id']})

        if len(answers):
            for k, v in answers.items():
                for answer_list in v:
                    yield {
                        "uuid": str(uuid.uuid4()),
                        'answer': answer_list,
                        'dataRow': {
                            "id": data_row_id
                        },
                        "schemaId": k
                    }

    def get_ontology_info(self, model_id):
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
                    "parent_feature_schema_id": tool.feature_schema_id
                } for option in tool.options
            })
        return options

    def export_model_run_labels(self, model_run_id):
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
            row['media_type'] = 'text'
        return LBV1Converter.deserialize(contents)

    def run(self, etl_file: str, model_run_id: str, model: Model,
            job_name: str):
        bucket_name, key = self.parse_uri(etl_file)
        source_uri = self.build_inference_file(bucket_name, key)
        nowgmt = time.strftime("%Y-%m-%d_%H:%M:%S", time.gmtime())
        destination = f"gs://{bucket_name}/inference/text-{self.classification_type}-classification/{nowgmt}/"

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
        annotation_data = []

        model_run = self.lb_client._get_single(ModelRun, model_run_id)
        options = self.get_ontology_info(model_run.model_id)
        for batch in batch_prediction_job.iter_outputs():
            for prediction_data in ndjson.loads(batch.download_as_string()):
                prediction = prediction_data['prediction']
                # only way to get data row id is to lookup from the content uri
                data_row_id = prediction_data['instance']['content'].split(
                    "/")[-1].replace(".txt", "")
                if self.classification_type == 'single':
                    annotation_data.append(
                        self.build_upload_data_single(prediction, options,
                                                      data_row_id))
                else:
                    annotation_data.extend(
                        self.build_upload_data_multi(prediction, options,
                                                     data_row_id))

        predictions = list(NDJsonConverter.deserialize(annotation_data))
        labels = self.export_model_run_labels(model_run_id)
        self.compute_metrics(labels, predictions, options)
        upload_task = model_run.add_predictions(
            f'diagnostics-import-{uuid.uuid4()}',
            NDJsonConverter.serialize(predictions))
        upload_task.wait_until_done()
        print(
            f"IMPORT ERRORS : {upload_task.errors}. Imported {len(predictions)}"
        )
        logger.info(
            f"IMPORT ERRORS : {upload_task.errors}. Imported {len(predictions)}"
        )
        return JobStatus(JobState.SUCCESS)

    def compute_metrics(self, labels, predictions, options):
        pairs = get_label_pairs(labels, predictions, filter_mismatch=True)
        for (ground_truth, prediction) in pairs.values():
            # Assign names instead of feature ids for classes.
            for annotation in prediction.annotations:
                # Unused for classifications so actually doesn't matter.
                # Only needed so that all pairs have names.
                self.add_name_to_annotation(annotation, options)
            metrics = []
            metrics.extend(
                feature_confusion_matrix_metric(ground_truth.annotations,
                                                prediction.annotations))

            prediction.annotations.extend(metrics)

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


class TextClassificationPipeline(Pipeline):

    def __init__(self, text_classification_type: TextClassificationType,
                 lb_api_key: str, gcs_bucket: str, service_account_email: str,
                 google_cloud_project: str):
        self.etl_job = TextClassificationETL(text_classification_type,
                                             gcs_bucket, service_account_email,
                                             google_cloud_project)
        self.training_job = TextClassificationTraining(text_classification_type)
        self.deployment = TextClassificationDeployment()
        self.inference = TextClassificationInference(lb_api_key,
                                                     text_classification_type)

    def parse_args(self, json_data: Dict[str, Any]) -> str:
        # Any validation goes here
        model_run_id = json_data['model_run_id']
        job_name = json_data['job_name']
        return model_run_id, job_name

    def run(self, json_data):
        model_run_id, job_name = self.parse_args(json_data)
        etl_status = self.etl_job.run(model_run_id, job_name)
        # Report state and training data uri to labelbox
        logger.info(f"ETL Status: {etl_status}")
        if etl_status.state == JobState.FAILED:
            logger.info(f"Job failed. Exiting.")
            return

        training_status = self.training_job.run(etl_status.result, job_name)
        # Report state and model id to labelbox
        logger.info(f"Training Status: {training_status}")
        if training_status.state == JobState.FAILED:
            logger.info(f"Job failed. Exiting.")
            return

        deployment_status = self.deployment.run(training_status.result['model'],
                                                job_name)
        # Report state and model id to labelbox
        logger.info(f"Deployment Status: {deployment_status}")
        if deployment_status.state == JobState.FAILED:
            logger.info(f"Job failed. Exiting.")
            return

        inference_status = self.inference.run(etl_status.result, model_run_id,
                                              training_status.result['model'],
                                              job_name)
        # Report state and model id to labelbox
        logger.info(f"Inference Status: {inference_status}")
        if inference_status.state == JobState.FAILED:
            logger.info(f"Job failed. Exiting.")
            return


class TextSingleClassificationPipeline(TextClassificationPipeline):

    def __init__(self, lb_api_key, gcs_bucket: str, service_account_email: str,
                 google_cloud_project: str):
        super().__init__('single', lb_api_key, gcs_bucket,
                         service_account_email, google_cloud_project)


class TextMultiClassificationPipeline(TextClassificationPipeline):

    def __init__(self, lb_api_key: str, gcs_bucket: str,
                 service_account_email: str, google_cloud_project: str):
        super().__init__('multi', lb_api_key, gcs_bucket, service_account_email,
                         google_cloud_project)
