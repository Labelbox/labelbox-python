import os
from typing import TypedDict, Union, Literal
import json

from google.cloud import aiplatform

from etl.images.bounding_box_etl import BoundingBoxETL
from etl.text.ner_etl import NERETL
from training.images.bounding_box_training import BoundingBoxTraining
from training.text.ner_training import NERTraining
from job import Job

labelbox_api_key = os.environ['LABELBOX_API_KEY']
gcs_bucket = os.environ['GCS_BUCKET']
gc_cred_path = os.environ['GOOGLE_APPLICATION_CREDENTIALS']

with open(gc_cred_path, 'r') as file:
    project_id = json.load(file)['project_id']

aiplatform.init(project=project_id, staging_bucket=f"gs://{gcs_bucket}")


class Pipeline(TypedDict):
    etl: Job
    train: Job


class Pipelines(TypedDict):
    bounding_box: Pipeline
    ner: Pipeline


pipelines: Pipelines = {
    'bounding_box': {
        'etl': BoundingBoxETL(gcs_bucket, labelbox_api_key, gc_cred_path),
        'train': BoundingBoxTraining()
    },
    'ner': {
        'etl': NERETL(gcs_bucket, labelbox_api_key, gc_cred_path),
        'train': NERTraining()
    }
}
PipelineName = Union[Literal['bounding_box', 'ner']]

if set(PipelineName.__args__) != set(pipelines.keys()):
    raise ValueError(
        "The keys in `pipelines` must match all names in PipelineName")
