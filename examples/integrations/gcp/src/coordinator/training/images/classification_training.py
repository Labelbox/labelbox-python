from typing import Any, Dict
from uuid import uuid4
import logging

from job import Job, JobStatus, JobState
from google.cloud import aiplatform

logger = logging.getLogger("uvicorn")


class ClassificationTraining(Job):

    def __init__(self, multi_classification: bool):
        self.multi_classification = multi_classification

    def parse_args(self, json_data: Dict[str, Any]) -> str:
        if 'training_file_uri' not in json_data:
            raise ValueError("Expected param training_file_uri")
        return json_data['training_file_uri']

    def run_local(self, json_data: Dict[str, Any]) -> JobStatus:
        training_file_uri = self.parse_args(json_data)
        display_name = f"image_{'multi' if self.multi_classification else 'single'}_classification_{uuid4()}"
        dataset = aiplatform.ImageDataset.create(
            display_name=display_name,
            gcs_source=[training_file_uri],
            import_schema_uri=aiplatform.schema.dataset.ioformat.image.
            single_label_classification if not self.multi_classification else
            aiplatform.schema.dataset.ioformat.image.multi_label_classification)
        job = aiplatform.AutoMLImageTrainingJob(
            display_name=display_name,
            prediction_type="classification",
            multi_label=self.multi_classification,
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


class SingleClassificationTraining(ClassificationTraining):

    def __init__(self):
        super().__init__(False)


class MultiClassificationTraining(ClassificationTraining):

    def __init__(self):
        super().__init__(True)
