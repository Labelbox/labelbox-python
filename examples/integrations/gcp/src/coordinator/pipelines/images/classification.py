from typing import Dict, Any
import time
import logging

from google.cloud import aiplatform
from google.cloud.aiplatform import Model

from pipelines.types import Pipeline, JobStatus, JobState, Job, \
    ClassificationInferenceJob, ClassificationType, PipelineState

logger = logging.getLogger("uvicorn")


class ImageClassificationETL(Job):

    def __init__(self, deployment_name: str,
                 classification_type: ClassificationType, gcs_bucket: str,
                 service_account_email: str, google_cloud_project: str):
        self.classification_type = classification_type
        self.gcs_bucket = gcs_bucket
        self.service_account_email = service_account_email
        self.google_cloud_project = google_cloud_project
        self.container_name = f"gcr.io/{google_cloud_project}/{deployment_name}/image_classification_etl"

    def run(self, model_run_id: str, job_name: str) -> JobStatus:
        nowgmt = time.strftime("%Y-%m-%d_%H:%M:%S", time.gmtime())
        gcs_key = f'etl/image-{self.classification_type}-classification/{nowgmt}.jsonl'
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


class ClassificationTraining(Job):

    def __init__(self, classification_type: ClassificationType):
        self.classification_type = classification_type
        if classification_type == 'single':
            self.multi_label = False
            self.import_schema_uri = aiplatform.schema.dataset.ioformat.image.single_label_classification
        elif classification_type == 'multi':
            self.multi_label = True
            self.import_schema_uri = aiplatform.schema.dataset.ioformat.image.multi_label_classification
        else:
            raise ValueError(
                f"Unexpected classification type: `{classification_type}`")

    def run(self, training_file_uri: str, job_name: str) -> JobStatus:
        dataset = aiplatform.ImageDataset.create(
            display_name=job_name,
            gcs_source=[training_file_uri],
            import_schema_uri=self.import_schema_uri)
        job = aiplatform.AutoMLImageTrainingJob(
            display_name=job_name,
            prediction_type="classification",
            multi_label=self.multi_label,
            model_type="MOBILE_TF_LOW_LATENCY_1")
        model = job.run(
            dataset=dataset,
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


class ImageClassificationDeployment(Job):

    def run(self, model: Model, job_name: str) -> JobStatus:
        endpoint = model.deploy(deployed_model_display_name=job_name)
        return JobStatus(JobState.SUCCESS,
                         result={'endpoint_id': endpoint.name})


class ImageClassificationInference(ClassificationInferenceJob):

    def __init__(self, labelbox_api_key: str,
                 classification_type: ClassificationType):
        self.classification_threshold = 0.2
        super().__init__(labelbox_api_key, classification_type, 'image')


class ImageClassificationPipeline(Pipeline):

    def __init__(self, image_classification_type: ClassificationType,
                 deployment_name: str, lb_api_key: str, gcs_bucket: str,
                 service_account_email: str, google_cloud_project: str):

        self.image_classification_type = image_classification_type
        self.etl_job = ImageClassificationETL(deployment_name,
                                              image_classification_type,
                                              gcs_bucket, service_account_email,
                                              google_cloud_project)
        self.training_job = ClassificationTraining(image_classification_type)
        self.inference = ImageClassificationInference(
            lb_api_key, image_classification_type)
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


class ImageSingleClassificationPipeline(ImageClassificationPipeline):

    def __init__(self, deployment_name: str, lb_api_key: str, gcs_bucket: str,
                 service_account_email: str, google_cloud_project: str):
        super().__init__('single', deployment_name, lb_api_key, gcs_bucket,
                         service_account_email, google_cloud_project)


class ImageMultiClassificationPipeline(ImageClassificationPipeline):

    def __init__(self, deployment_name: str, lb_api_key: str, gcs_bucket: str,
                 service_account_email: str, google_cloud_project: str):
        super().__init__('multi', deployment_name, lb_api_key, gcs_bucket,
                         service_account_email, google_cloud_project)
