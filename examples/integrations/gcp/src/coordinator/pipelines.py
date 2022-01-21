import os
from etl.images.bounding_box_etl import BoundingBoxETL
from training.images.bounding_box_training_placeholder import BoundingBoxTraining

from typing import TypedDict, Union, Literal
from job import CustomJob, Job

labelbox_api_key = os.environ['LABELBOX_API_KEY']
gcs_bucket = os.environ['GCS_BUCKET']


class Pipeline(TypedDict):
    etl: CustomJob
    train: Job


class Pipelines(TypedDict):
    bounding_box: Pipeline


pipelines: Pipelines = {
    'bounding_box': {
        'etl': BoundingBoxETL(gcs_bucket, labelbox_api_key),
        'train': BoundingBoxTraining()
    }
}
pipeline_name = Union[Literal['bounding_box']]
