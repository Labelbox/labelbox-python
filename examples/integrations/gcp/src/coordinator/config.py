import os
from typing import TypedDict, Union, Literal
import json

from google.cloud import aiplatform

from pipelines.images.classification import ImageSingleClassificationPipeline, ImageMultiClassificationPipeline
from pipelines.images.bounding_box import BoundingBoxPipeline
from pipelines.types import Pipeline
from pipelines.text.ner import NERPipeline
from pipelines.text.classification import TextSingleClassificationPipeline, TextMultiClassificationPipeline

# Any env vars should be declared here so that we can check if they are set on startup

# Used for config
_labelbox_api_key = os.environ['LABELBOX_API_KEY']
_gcs_bucket = os.environ['GCS_BUCKET']
_gc_cred_path = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
_gc_config_dir = os.environ['GCLOUD_CONFIG_DIR']

# Used elsewhere (Should only be used for server env vars. Everything else should be passed through)
WEBHOOK_SECRET = os.environ['WEBHOOK_SECRET']

with open(_gc_cred_path, 'r') as file:
    project_id = json.load(file)['project_id']

aiplatform.init(project=project_id, staging_bucket=f"gs://{_gcs_bucket}")


class Pipelines(TypedDict):
    bounding_box: Pipeline
    ner: Pipeline
    image_single_classification: Pipeline
    image_multi_classification: Pipeline
    text_single_classification: Pipeline
    text_multi_classification: Pipeline


_common_params = [_gcs_bucket, _labelbox_api_key, _gc_cred_path, _gc_config_dir]
pipelines: Pipelines = {
    'bounding_box':
        BoundingBoxPipeline(*_common_params),
    'ner':
        NERPipeline(*_common_params),
    'image_single_classification':
        ImageSingleClassificationPipeline(*_common_params),
    'image_multi_classification':
        ImageMultiClassificationPipeline(*_common_params),
    'text_single_classification':
        TextSingleClassificationPipeline(*_common_params),
    'text_multi_classification':
        TextMultiClassificationPipeline(*_common_params),
}

PipelineName = Union[Literal['bounding_box', 'ner',
                             'image_single_classification',
                             'image_multi_classification',
                             'text_single_classification',
                             'text_multi_classification']]

if set(PipelineName.__args__) != set(pipelines.keys()):
    raise ValueError(
        "The keys in `pipelines` must match all names in PipelineName")
