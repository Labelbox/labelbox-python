from typing import Dict, Any
import time
import logging

from google.cloud import aiplatform

from pipelines.types import Pipeline, CustomJob, JobStatus, JobState, Job

logger = logging.getLogger("uvicorn")


class BoundingBoxETL(CustomJob):

    def __init__(self, gcs_bucket: str, labelbox_api_key: str,
                 gc_cred_path: str, gc_config_dir: str):
        self.gcs_bucket = gcs_bucket
        self.labelbox_api_key = labelbox_api_key
        self.gc_cred_path = gc_cred_path
        self.gc_config_dir = gc_config_dir

        super().__init__(name="bounding_box_etl",
                         local_container_name="gcp_bounding_box_etl")

    def run_local(self, project_id: str) -> JobStatus:
        nowgmt = time.strftime("%Y-%m-%d_%H:%M:%S", time.gmtime())
        gcs_key = f'etl/bounding-box/{nowgmt}.jsonl'
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


class BoundingBoxTraining(Job):

    def parse_args(self, json_data: Dict[str, Any]) -> str:
        if 'training_file_uri' not in json_data:
            raise ValueError("Expected param training_file_uri")
        return json_data['training_file_uri']

    def run_local(self, training_file_uri: str, job_name: str) -> JobStatus:
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
        return JobStatus(JobState.SUCCESS, result={'model_id': model.name})

    def run_remote(self, training_data_uri):
        ...


class BoundingBoxPipeline(Pipeline):

    def __init__(self, gcs_bucket: str, labelbox_api_key: str,
                 gc_cred_path: str, gc_config_dir: str):
        self.etl_job = BoundingBoxETL(gcs_bucket, labelbox_api_key,
                                      gc_cred_path, gc_config_dir)
        self.training_job = BoundingBoxTraining()

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

    def run_remote(self, *args, **kwargs):
        raise NotImplementedError("")
