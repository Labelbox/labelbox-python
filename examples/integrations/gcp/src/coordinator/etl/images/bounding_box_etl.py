import os
from typing import Dict, Any
import time
import uuid

from job import CustomJob, JobStatus


class BoundingBoxETL(CustomJob):

    def __init__(self, gcs_bucket: str, labelbox_api_key: str,
                 gc_cred_path: str):
        self.gcs_bucket = gcs_bucket
        self.labelbox_api_key = labelbox_api_key
        self.gc_cred_path = gc_cred_path
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

        # TODO: how to version image datasets (and training)... We don't want to re-create the same data every time..
        # Answer: For both of these, the webhook should post the name of the run... That way we can always have a new name
        # and it is
        return job_status
