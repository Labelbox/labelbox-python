import os
import logging

from job import CustomJob, JobStatus

logger = logging.getLogger(__name__)


class BoundingBoxETL(CustomJob):

    def __init__(self):
        # TODO: When we add vertex we will want to use gcr uris instead of local names
        super().__init__(name="bounding_box_etl",
                         container_name="gcp_bounding_box_etl")

    def run_local(self, project_id, gcs_bucket, gcs_key, labelbox_api_key,
                  docker_client) -> JobStatus:
        return super().run_local(
            docker_client,
            cmd=[
                f"--gcs_bucket={gcs_bucket}", f"--project_id={project_id}",
                f"--gcs_key={gcs_key}"
            ],
            env_vars=[
                "GOOGLE_APPLICATION_CREDENTIALS=/root/.config/gcloud/development-sa-creds.json",
                f"LABELBOX_API_KEY={labelbox_api_key}"
            ],
            volumes={
                os.environ['GCLOUD_CONFIG_DIR']: {
                    'bind': '/root/.config/gcloud',
                    'mode': 'ro'
                }
            })
