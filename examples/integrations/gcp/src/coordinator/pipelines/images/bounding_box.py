from typing import Dict, Any
import time
import logging
import uuid

from google.cloud import aiplatform
from labelbox.data.serialization import NDJsonConverter
from labelbox.data.metrics.group import get_label_pairs
from labelbox.data.metrics import feature_confusion_matrix_metric
from labelbox.data.annotation_types import Rectangle
from labelbox import ModelRun
import ndjson

from pipelines.types import Pipeline, JobStatus, JobState, Job, \
    InferenceJob, PipelineState

logger = logging.getLogger("uvicorn")


class BoundingBoxETL(Job):

    def __init__(self, deployment_name: str, gcs_bucket: str,
                 service_account_email: str, google_cloud_project: str):
        self.gcs_bucket = gcs_bucket
        self.service_account_email = service_account_email
        self.google_cloud_project = google_cloud_project
        self.container_name = f"gcr.io/{google_cloud_project}/{deployment_name}/bounding_box_etl"

    def run(self, model_run_id: str, job_name: str) -> JobStatus:
        nowgmt = time.strftime("%Y-%m-%d_%H:%M:%S", time.gmtime())
        gcs_key = f'etl/bounding-box/{nowgmt}.jsonl'
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


class BoundingBoxTraining(Job):

    def run(self, training_file_uri: str, job_name: str) -> JobStatus:
        dataset = aiplatform.ImageDataset.create(
            display_name=job_name,
            gcs_source=[training_file_uri],
            import_schema_uri=aiplatform.schema.dataset.ioformat.image.
            bounding_box)
        job = aiplatform.AutoMLImageTrainingJob(
            display_name=job_name,
            prediction_type="object_detection",
            model_type="MOBILE_TF_LOW_LATENCY_1")
        model = job.run(
            dataset=dataset,
            # Every 1,000 is 1 node-hour. This is close to the minimum (20k).
            # Increase / parameterize this before deploying
            budget_milli_node_hours=1000,
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


class BoundingBoxDeployment(Job):

    def run(self, model: aiplatform.Model, job_name: str) -> JobStatus:
        endpoint = model.deploy(deployed_model_display_name=job_name)
        return JobStatus(JobState.SUCCESS,
                         result={'endpoint_id': endpoint.name})


class BoundingBoxInference(InferenceJob):

    def __init__(self, labelbox_api_key: str):
        self.confidence_threshold = 0.5
        super().__init__(labelbox_api_key)

    def build_inference_file(self, bucket_name, key):
        bucket = self.storage_client.get_bucket(bucket_name)
        # Create a blob object from the filepath
        blob = bucket.blob(key)
        contents = ndjson.loads(blob.download_as_string())
        prediction_inputs = []
        for line in contents:
            prediction_inputs.append({
                "content": line['imageGcsUri'],
                "mimeType": "text/plain",
            })
        nowgmt = time.strftime("%Y-%m-%d_%H:%M:%S", time.gmtime())
        blob = bucket.blob(f"inference_file/bounding-box/{nowgmt}.jsonl")
        blob.upload_from_string(data=ndjson.dumps(prediction_inputs),
                                content_type="application/jsonl")
        return f"gs://{bucket.name}/{blob.name}"

    def run(self, etl_file: str, model_run_id: str, model: aiplatform.Model,
            job_name: str):
        batch_prediction_job = self.batch_predict(etl_file, model, job_name,
                                                  'bounding-box')
        model_run = self.lb_client._get_single(ModelRun, model_run_id)
        tools = self.get_tool_info(model_run.model_id)
        annotation_data = list(
            self.process_predictions(batch_prediction_job, tools))
        predictions = list(NDJsonConverter.deserialize(annotation_data))
        labels = self.export_model_run_labels(model_run_id, 'image')
        self.compute_metrics(labels, predictions, tools)
        upload_task = model_run.add_predictions(
            f'diagnostics-import-{uuid.uuid4()}',
            NDJsonConverter.serialize(predictions))
        upload_task.wait_until_done()
        logger.info(
            f"IMPORT ERRORS : {upload_task.errors}. Imported {len(predictions)}"
        )
        return JobStatus(JobState.SUCCESS)

    def compute_metrics(self, labels, predictions, tools):
        tool_name_lookup = {v: k for k, v in tools.items()}
        pairs = get_label_pairs(labels, predictions, filter_mismatch=True)
        for (ground_truth, prediction) in pairs.values():
            for annotation in prediction.annotations:
                if isinstance(annotation.value, Rectangle):
                    annotation.name = tool_name_lookup[
                        annotation.feature_schema_id].replace(' ', '-')
            prediction.annotations.extend(
                feature_confusion_matrix_metric(ground_truth.annotations,
                                                prediction.annotations))

    def process_predictions(self, batch_prediction_job, tools):
        for batch in batch_prediction_job.iter_outputs():
            for prediction_data in ndjson.loads(batch.download_as_string()):
                if 'error' in prediction_data:
                    logger.info(f"Row failed. {prediction_data}")
                    continue

                file_name = prediction_data['instance']['content'].split(
                    "/")[-1].replace(".jpg", "")
                data_row_id, w, h = file_name.split("_")
                predictions = prediction_data['prediction']
                for display_name, confidence, bbox in zip(
                        predictions['displayNames'], predictions['confidences'],
                        predictions['bboxes']):
                    if confidence < self.confidence_threshold:
                        continue
                    x0_unscaled, x1_unscaled, y0_unscaled, y1_unscaled = bbox
                    x0, y0, x1, y1 = x0_unscaled * int(w), y0_unscaled * int(
                        h), x1_unscaled * int(w), y1_unscaled * int(h)
                    yield {
                        "uuid": str(uuid.uuid4()),
                        'dataRow': {
                            'id': data_row_id
                        },
                        'schemaId': tools[display_name],
                        'bbox': {
                            'top': y0,
                            'left': x0,
                            'height': y1 - y0,
                            'width': x1 - x0
                        }
                    }


class BoundingBoxPipeline(Pipeline):

    def __init__(self, deployment_name: str, lb_api_key: str, gcs_bucket: str,
                 service_account_email: str, google_cloud_project: str):
        self.etl_job = BoundingBoxETL(deployment_name, gcs_bucket,
                                      service_account_email,
                                      google_cloud_project)
        self.training_job = BoundingBoxTraining()
        self.inference = BoundingBoxInference(lb_api_key)
        super().__init__(lb_api_key)

    def parse_args(self, json_data: Dict[str, Any]) -> str:
        # Any validation goes here
        model_run_id = json_data['model_run_id']
        job_name = json_data['job_name']
        return model_run_id, job_name

    def run(self, json_data):
        model_run_id, job_name = self.parse_args(json_data)

        self.update_status(PipelineState.PREPARING_DATA, model_run_id)
        etl_status = self.run_job(
            model_run_id, lambda: self.etl_job.run(model_run_id, job_name))
        if etl_status is None:
            return

        self.update_status(PipelineState.TRAINING_MODEL,
                           model_run_id,
                           metadata={'training_data_input': etl_status.result})

        training_status = self.run_job(
            model_run_id,
            lambda: self.training_job.run(etl_status.result, job_name))

        if training_status is None:
            return
        self.update_status(
            PipelineState.TRAINING_MODEL,
            model_run_id,
            metadata={'model_id': training_status.result['model'].name})

        inference_status = self.run_job(
            model_run_id, lambda: self.inference.run(
                etl_status.result, model_run_id, training_status.result[
                    'model'], job_name))
        if inference_status is not None:
            self.update_status(PipelineState.COMPLETE, model_run_id)
