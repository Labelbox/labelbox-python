from typing import Dict, Any
import time
import logging

from google.cloud import aiplatform
from google.cloud.aiplatform import Model

from pipelines.types import Pipeline, CustomJob, JobStatus, JobState, Job

logger = logging.getLogger("uvicorn")


class NERETL(CustomJob):

    def __init__(self, gcs_bucket: str, labelbox_api_key: str,
                 gc_cred_path: str, gc_config_dir: str):
        self.gcs_bucket = gcs_bucket
        self.labelbox_api_key = labelbox_api_key
        self.gc_cred_path = gc_cred_path
        self.gc_config_dir = gc_config_dir
        super().__init__(name="ner_etl", local_container_name="gcp_ner_etl")

    def run_local(self, project_id: str) -> JobStatus:
        nowgmt = time.strftime("%Y-%m-%d_%H:%M:%S", time.gmtime())
        gcs_key = f'etl/ner/{nowgmt}.jsonl'
        job_status = self._run_local(
            cmd=[
                f"--gcs_bucket={self.gcs_bucket}", f"--project_id={project_id}",
                f"--gcs_key={gcs_key}"
            ],
            env_vars=[
                f"GOOGLE_APPLICATION_CREDENTIALS={self.gc_cred_path}",
                f"LABELBOX_API_KEY={self.labelbox_api_key}"
            ],
            volumes={
                self.gc_config_dir: {
                    'bind': '/root/.config/gcloud',
                    'mode': 'ro'
                }
            })
        job_status.result = f'gs://{self.gcs_bucket}/{gcs_key}'
        return job_status


class NERTraining(Job):

    def run_local(self, training_file_uri: str, job_name: str) -> JobStatus:
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
        return JobStatus(JobState.SUCCESS, result={'model_id': model.name})

    def run_remote(self, training_data_uri):
        ...


class TextNERDeployment(Job):

    def _run(self, model: Model, job_name: str) -> JobStatus:
        endpoint = model.deploy(deployed_model_display_name=job_name,
                                min_replica_count=1,
                                max_replica_count=5)
        # All we need is the endpoint id (aka name)
        return JobStatus(JobState.SUCCESS,
                         result={'endpoint_id': endpoint.name})

    def run_local(self, model: Model, job_name: str) -> JobStatus:
        return self._run(model, job_name)

    def run_remote(self, model: Model, job_name: str) -> JobStatus:
        return self._run(model, job_name)


class NERPipeline(Pipeline):

    def __init__(self, gcs_bucket: str, labelbox_api_key: str,
                 gc_cred_path: str, gc_config_dir: str):
        self.etl_job = NERETL(gcs_bucket, labelbox_api_key, gc_cred_path,
                              gc_config_dir)
        self.training_job = NERTraining()
        self.deployment = TextNERDeployment()

    def parse_args(self, json_data: Dict[str, Any]) -> str:
        # Any validation goes here
        project_id = json_data['project_id']
        job_name = json_data['job_name']
        return project_id, job_name

    def run_local(self, json_data):
        project_id, job_name = self.parse_args(json_data)
        etl_status = self.etl_job.run_local(project_id)
        # Report state and training data uri to labelbox
        logger.info(f"ETL Status: {etl_status}")
        if etl_status.state == JobState.FAILED:
            logger.info(f"Job failed. Exiting.")
            return

        training_status = self.training_job.run_local(etl_status.result,
                                                      job_name)
        # Report state and model id to labelbox
        logger.info(f"Training Status: {training_status}")
        if training_status.state == JobState.FAILED:
            logger.info(f"Job failed. Exiting.")
            return

        deployment_status = self.deployment.run_local(training_status.result,
                                                      job_name)
        # Report state and model id to labelbox
        logger.info(f"Deployment Status: {deployment_status}")
        if deployment_status.state == JobState.FAILED:
            logger.info(f"Job failed. Exiting.")
            return

    def run_remote(self, *args, **kwargs):
        raise NotImplementedError("")
