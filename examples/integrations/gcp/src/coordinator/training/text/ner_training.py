from typing import Any, Dict
import logging

from job import Job, JobStatus, JobState
from google.cloud import aiplatform
from uuid import uuid4

logger = logging.getLogger("uvicorn")


class NERTraining(Job):

    def parse_args(self, json_data: Dict[str, Any]) -> str:
        if 'training_file_uri' not in json_data:
            raise ValueError("Expected param training_file_uri")
        return json_data['training_file_uri']

    def run_local(self, json_data: Dict[str, Any]) -> JobStatus:
        training_file_uri = self.parse_args(json_data)
        dataset_display_name = f"ner_{uuid4()}"

        dataset = aiplatform.TextDataset.create(
            display_name=dataset_display_name,
            gcs_source=[training_file_uri],
            import_schema_uri=aiplatform.schema.dataset.ioformat.text.
            extraction,
        )

        job = aiplatform.AutoMLTextTrainingJob(
            display_name="matt-test-train-automl-text",
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
