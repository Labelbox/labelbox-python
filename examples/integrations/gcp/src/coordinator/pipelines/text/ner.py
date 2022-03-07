from typing import Dict, Any
import time
import logging
import uuid

from google.cloud import aiplatform
from google.cloud.aiplatform import Model

from pipelines.types import Pipeline, JobStatus, JobState, Job, InferenceJob

logger = logging.getLogger("uvicorn")

import ndjson
from labelbox import ModelRun
from labelbox.data.serialization import NDJsonConverter
from labelbox.data.metrics.group import get_label_pairs
from labelbox.data.annotation_types import TextEntity


class NERETL(Job):

    def __init__(self, gcs_bucket: str, service_account_email: str,
                 google_cloud_project: str):
        self.gcs_bucket = gcs_bucket
        self.service_account_email = service_account_email
        self.google_cloud_project = google_cloud_project
        self.container_name = f"gcr.io/{google_cloud_project}/training-repo/ner_etl"

    def run(self, model_run_id: str, job_name) -> JobStatus:
        nowgmt = time.strftime("%Y-%m-%d_%H:%M:%S", time.gmtime())
        gcs_key = f'etl/ner/{nowgmt}.jsonl'
        CMDARGS = [
            f"--gcs_bucket={self.gcs_bucket}", f"--model_run_id={model_run_id}",
            f"--gcs_key={gcs_key}"
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


class NERTraining(Job):

    def run(self, training_file_uri: str, job_name: str) -> JobStatus:
        dataset = aiplatform.TextDataset.create(
            display_name=job_name,
            gcs_source=[training_file_uri],
            import_schema_uri=aiplatform.schema.dataset.ioformat.text.
            extraction,
        )

        job = aiplatform.AutoMLTextTrainingJob(display_name=job_name,
                                               prediction_type="extraction")

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


class TextNERDeployment(Job):

    def run(self, model: Model, job_name: str) -> JobStatus:
        endpoint = model.deploy(deployed_model_display_name=job_name)
        return JobStatus(JobState.SUCCESS,
                         result={'endpoint_id': endpoint.name})


class NERInference(InferenceJob):

    def __init__(self, lb_api_key: str):
        # This will eventually be run as an external job.
        # Keeping it here for now since the inferences are still run as a separate job
        super().__init__(lb_api_key)

    def build_inference_file(self, bucket_name, key):
        bucket = self.storage_client.get_bucket(bucket_name)
        # Create a blob object from the filepath
        blob = bucket.blob(key)
        contents = ndjson.loads(blob.download_as_string())
        prediction_inputs = []
        for line in contents:
            prediction_inputs.append({
                "content": line['textContent'],
                "mimeType": "text/plain",
                "key": line['dataItemResourceLabels']['dataRowId']
            })

        nowgmt = time.strftime("%Y-%m-%d_%H:%M:%S", time.gmtime())
        blob = bucket.blob(f"inference_file/ner/{nowgmt}.jsonl")
        blob.upload_from_string(data=ndjson.dumps(prediction_inputs),
                                content_type="application/jsonl")
        return f"gs://{bucket.name}/{blob.name}"

    def process_predictions(self, batch_prediction_job, tools):
        for batch in batch_prediction_job.iter_outputs():
            for prediction_data in ndjson.loads(batch.download_as_string()):
                if 'error' in prediction_data:
                    logger.info(f"Row failed. {prediction_data}")
                    continue

                data_row_id = prediction_data['key']
                prediction = prediction_data['prediction']

                if not len(prediction):
                    # No prediction..
                    continue

                for name, start, end in zip(
                        prediction['displayNames'],
                        prediction['textSegmentStartOffsets'],
                        prediction['textSegmentEndOffsets']):
                    start = int(start)  # Start is inclusive
                    end = int(
                        end
                    ) + 1  # vertex end is inclusive. We want exclusive for labelbox
                    yield {
                        'uuid': str(uuid.uuid4()),
                        'dataRow': {
                            'id': data_row_id
                        },
                        'schemaId': tools[name],
                        'location': {
                            'start': start,
                            'end': end
                        }
                    }

    def run(self, etl_file: str, model_run_id: str, model: Model,
            job_name: str):
        batch_prediction_job = self.batch_predict(etl_file, model, job_name,
                                                  "ner")
        model_run = self.lb_client._get_single(ModelRun, model_run_id)
        tools = self.get_tool_info(model_run.model_id)
        annotation_data = list(
            self.process_predictions(batch_prediction_job, tools))
        predictions = list(NDJsonConverter.deserialize(annotation_data))
        labels = self.export_model_run_labels(model_run_id, 'text')
        self.compute_metrics(labels, predictions, tools)
        upload_task = model_run.add_predictions(
            f'diagnostics-import-{uuid.uuid4()}',
            NDJsonConverter.serialize(predictions))
        upload_task.wait_until_done()
        # TODO: Report errors without necessarily breaking the job...
        logger.info(
            f"IMPORT ERRORS : {upload_task.errors}. Imported {len(predictions)}"
        )
        return JobStatus(JobState.SUCCESS)

    def compute_metrics(self, labels, predictions, tools):
        tool_name_lookup = {v: k for k, v in tools.items()}
        pairs = get_label_pairs(labels, predictions, filter_mismatch=True)
        for (ground_truth, prediction) in pairs.values():
            # Assign names instead of feature ids for classes.
            for annotation in prediction.annotations:
                # Unused for classifications so actually doesn't matter.
                # Only needed so that all pairs have names.
                if isinstance(annotation.value, TextEntity):
                    annotation.name = tool_name_lookup[
                        annotation.feature_schema_id].replace(' ', '-')
            # TODO: Metrics are not yet supported for TextEntity
            #metrics = []
            #prediction.annotations.extend(metrics)


class NERPipeline(Pipeline):

    def __init__(self, lb_api_key: str, gcs_bucket: str,
                 service_account_email: str, google_cloud_project: str):
        self.etl_job = NERETL(gcs_bucket, service_account_email,
                              google_cloud_project)
        self.training_job = NERTraining()
        self.deployment = TextNERDeployment()
        self.inference = NERInference(lb_api_key)

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
