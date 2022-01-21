from typing import Any, Dict
import logging

from job import Job, JobStatus
from google.cloud import aiplatform
from uuid import uuid4

logger = logging.getLogger("uvicorn")


class BoundingBoxTraining(Job):

    def parse_args(self, json_data: Dict[str, Any]) -> str:
        if 'training_file_uri' not in json_data:
            raise ValueError("Expected param training_file_uri")
        return json_data['training_file_uri']

    def run_local(self, json_data: Dict[str, Any]) -> JobStatus:
        training_file_uri = self.parse_args(json_data)
        dataset_display_name = f"bounding_box_{uuid4()}"
        dataset = aiplatform.ImageDataset.create(
            display_name=dataset_display_name,
            gcs_source=[training_file_uri],
            import_schema_uri=aiplatform.schema.dataset.ioformat.image.
            bounding_box)
        job = aiplatform.AutoMLImageTrainingJob(
            display_name="matt-test-train-automl",
            prediction_type="object_detection",
            model_type=
            "MOBILE_TF_LOW_LATENCY_1"  # lower accuracy but should train quicker while we build this out
        )

        model = job.run(
            dataset=dataset,
            # Every 1,000 is 1 node-hour. This is close to the minimum (20k).
            # Increase / parameterize this before deploying
            budget_milli_node_hours=30_000,
        )

        logging.info("model uri %s" % model.uri)

    def run_remote(self, training_data_uri):
        ...
