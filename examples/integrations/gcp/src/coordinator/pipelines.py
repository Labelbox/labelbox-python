import os
from etl.images.bounding_box_etl import BoundingBoxETL
from training.images.bounding_box_training_placeholder import BoundingBoxTraining

from typing import TypedDict, Union, Literal
from job import Job

labelbox_api_key = os.environ['LABELBOX_API_KEY']
gcs_bucket = os.environ['GCS_BUCKET']


class Pipeline(TypedDict):
    etl: Job
    train: Job


class Pipelines(TypedDict):
    bounding_box: Pipeline


pipelines: Pipelines = {
    'bounding_box': {
        'etl': BoundingBoxETL(gcs_bucket, labelbox_api_key),
        'train': BoundingBoxTraining()
    }
}
PipelineName = Union[Literal['bounding_box']]

if set(PipelineName.__args__) != set(pipelines.keys()):
    raise ValueError(
        "The keys in `pipelines` must match all names in PipelineName")
