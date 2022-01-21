import os
from typing import Dict, Any
import time

from job import CustomJob, JobStatus


class BoundingBoxETL(CustomJob):

    def __init__(self, gcs_bucket: str, labelbox_api_key: str):
        self.gcs_bucket = gcs_bucket
        self.labelbox_api_key = labelbox_api_key
        # TODO: When we add vertex we will want to use gcr uris instead of local names
        super().__init__(name="bounding_box_etl",
                         container_name="gcp_bounding_box_etl")

    def parse_args(self, json_data: Dict[str, Any]) -> str:
        # Any validation goes here
        project_id = json_data['project_id']
        return project_id

    def run_local(self, json_data: Dict[str, Any]) -> JobStatus:
        nowgmt = time.strftime("%Y-%m-%d_%H:%M:%S", time.gmtime())
        gcs_key = f'etl/bounding-box/{nowgmt}.jsonl'
        project_id = self.parse_args(json_data)
        job_status = self._run_local(
            cmd=[
                f"--gcs_bucket={self.gcs_bucket}", f"--project_id={project_id}",
                f"--gcs_key={gcs_key}"
            ],
            env_vars=[
                "GOOGLE_APPLICATION_CREDENTIALS=/root/.config/gcloud/development-sa-creds.json",
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
