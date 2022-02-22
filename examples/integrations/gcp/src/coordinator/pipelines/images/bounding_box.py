from typing import Dict, Any
import time
import logging

from google.cloud import aiplatform
from google.cloud.aiplatform.models import Model

from pipelines.types import Pipeline, JobStatus, JobState, Job

logger = logging.getLogger("uvicorn")


class BoundingBoxETL(Job):

    def __init__(self, gcs_bucket: str, service_account_email: str,
                 google_cloud_project: str):
        self.gcs_bucket = gcs_bucket
        self.service_account_email = service_account_email
        self.google_cloud_project = google_cloud_project
        self.container_name = f"gcr.io/{google_cloud_project}/training-repo/bounding_box_etl"

    def run(self, project_id: str, job_name: str) -> JobStatus:
        nowgmt = time.strftime("%Y-%m-%d_%H:%M:%S", time.gmtime())
        gcs_key = f'etl/bounding-box/{nowgmt}.jsonl'
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

    def run(self, model: Model, job_name: str) -> JobStatus:
        endpoint = model.deploy(deployed_model_display_name=job_name)
        return JobStatus(JobState.SUCCESS,
                         result={'endpoint_id': endpoint.name})


class BoundingBoxPipeline(Pipeline):

    def __init__(self, gcs_bucket: str, service_account_email: str,
                 google_cloud_project: str):
        self.etl_job = BoundingBoxETL(gcs_bucket, service_account_email,
                                      google_cloud_project)
        self.training_job = BoundingBoxTraining()
        self.deployment = BoundingBoxDeployment()

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

        logger.info(f"Deployment status: {deployment_status}")

    def run_remote(self, *args, **kwargs):
        raise NotImplementedError("")
