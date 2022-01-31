from typing import Dict, Any, Union, Literal
import time
import os

from job import CustomJob, JobStatus
import logging

ImageClassificationType = Union[Literal['single'], Literal['multi']]

logger = logging.getLogger("uvicorn")


class ImageClassificationETL(CustomJob):

    def __init__(self, classification_type: ImageClassificationType,
                 gcs_bucket: str, labelbox_api_key: str, gc_cred_path: str):
        self.classification_type = classification_type
        self.gcs_bucket = gcs_bucket
        self.labelbox_api_key = labelbox_api_key
        self.gc_cred_path = gc_cred_path
        super().__init__(name="image_classification",
                         container_name="gcp_image_classification")

    def parse_args(self, json_data: Dict[str, Any]) -> str:
        # Any validation goes here
        project_id = json_data['project_id']
        return project_id

    def run_local(self, json_data: Dict[str, Any]) -> JobStatus:
        nowgmt = time.strftime("%Y-%m-%d_%H:%M:%S", time.gmtime())
        gcs_key = f'etl/image-{self.classification_type}-classification/{nowgmt}.jsonl'
        project_id = self.parse_args(json_data)
        job_status = self._run_local(
            cmd=[
                f"--gcs_bucket={self.gcs_bucket}", f"--project_id={project_id}",
                f"--gcs_key={gcs_key}",
                f"--classification_type={self.classification_type}"
            ],
            env_vars=[
                f"GOOGLE_APPLICATION_CREDENTIALS={self.gc_cred_path}",
                f"LABELBOX_API_KEY={self.labelbox_api_key}"
            ],
            volumes={
                os.environ['GCLOUD_CONFIG_DIR']: {
                    'bind': '/root/.config/gcloud',
                    'mode': 'ro'
                }
            })
        job_status.result = {
            'training_file_uri': f'gs://{self.gcs_bucket}/{gcs_key}'
        }
        return job_status


class ImageSingleClassification(ImageClassificationETL):

    def __init__(self, gcs_bucket: str, labelbox_api_key: str,
                 gc_cred_path: str):
        super().__init__('single', gcs_bucket, labelbox_api_key, gc_cred_path)


class ImageMultiClassification(ImageClassificationETL):

    def __init__(self, gcs_bucket: str, labelbox_api_key: str,
                 gc_cred_path: str):
        super().__init__('multi', gcs_bucket, labelbox_api_key, gc_cred_path)
