from typing import Dict, Any, Union, Literal
import time
import logging

from google.cloud import aiplatform
from google.cloud.aiplatform import Model

from pipelines.types import Pipeline, JobStatus, JobState, Job

logger = logging.getLogger("uvicorn")

TextClassificationType = Union[Literal['single'], Literal['multi']]


class TextClassificationETL(Job):
    container_name = "gcr.io/sandbox-5500/training-repo/text_classification_etl"

    def __init__(self, classification_type: TextClassificationType,
                 gcs_bucket: str, service_account_email: str,
                 google_cloud_project: str):
        self.classification_type = classification_type
        self.gcs_bucket = gcs_bucket
        self.service_account_email = service_account_email
        self.google_cloud_project = google_cloud_project

    def run(self, project_id: str, job_name) -> JobStatus:
        nowgmt = time.strftime("%Y-%m-%d_%H:%M:%S", time.gmtime())
        gcs_key = f'etl/text-{self.classification_type}-classification/{nowgmt}.jsonl'
        CMDARGS = [
            f"--gcs_bucket={self.gcs_bucket}", f"--project_id={project_id}",
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


class TextClassificationPipeline(Pipeline):

    def __init__(self, text_classification_type: TextClassificationType,
                 gcs_bucket: str, service_account_email: str,
                 google_cloud_project: str):
        self.etl_job = TextClassificationETL(text_classification_type,
                                             gcs_bucket, service_account_email,
                                             google_cloud_project)
        self.training_job = TextClassificationTraining(text_classification_type)
        self.deployment = TextClassificationDeployment()

    def parse_args(self, json_data: Dict[str, Any]) -> str:
        # Any validation goes here
        project_id = json_data['project_id']
        job_name = json_data['job_name']
        return project_id, job_name

    def run_local(self, json_data):
        project_id, job_name = self.parse_args(json_data)
        etl_status = self.etl_job.run(project_id, job_name)
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

    def run_remote(self, *args, **kwargs):
        raise NotImplementedError("")


class TextSingleClassificationPipeline(TextClassificationPipeline):

    def __init__(self, gcs_bucket: str, service_account_email: str,
                 google_cloud_project: str):
        super().__init__('single', gcs_bucket, service_account_email,
                         google_cloud_project)


class TextMultiClassificationPipeline(TextClassificationPipeline):

    def __init__(self, gcs_bucket: str, service_account_email: str,
                 google_cloud_project: str):
        super().__init__('multi', gcs_bucket, service_account_email,
                         google_cloud_project)
