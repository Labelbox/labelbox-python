from typing import Any, Dict
from time import sleep

from job import Job, JobState, JobStatus


class BoundingBoxTraining(Job):
    # A dummy example that runs.

    def parse_args(self, json_data: Dict[str, Any]) -> str:
        if 'training_file_uri' not in json_data:
            raise ValueError("Expected param training_file_uri")
        return json_data['training_file_uri']

    def run_local(self, json_data: Dict[str, Any]) -> JobStatus:
        training_file_uri = self.parse_args(json_data)
        sleep(1)
        return JobStatus(JobState.SUCCESS)

    def run_remote(self, training_data_uri):
        ...
