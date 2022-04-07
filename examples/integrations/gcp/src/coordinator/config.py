import os
from typing import TypedDict, Union, Literal

from google.cloud import aiplatform
from google.cloud import secretmanager
import google.auth

from pipelines.images.classification import ImageSingleClassificationPipeline, ImageMultiClassificationPipeline
from pipelines.images.bounding_box import BoundingBoxPipeline
from pipelines.types import Pipeline
from pipelines.text.ner import NERPipeline
from pipelines.text.classification import TextSingleClassificationPipeline, TextMultiClassificationPipeline

service_account = os.environ["GOOGLE_SERVICE_ACCOUNT"]
google_cloud_project = os.environ['GOOGLE_PROJECT']
_deployment_name = os.environ['DEPLOYMENT_NAME']

client = secretmanager.SecretManagerServiceClient()

_labelbox_api_key = os.environ.get('LABELBOX_API_KEY')
if _labelbox_api_key is None:
    secret_id = f"{_deployment_name}_labelbox_api_key"
    name = f"projects/{google_cloud_project}/secrets/{secret_id}/versions/1"
    response = client.access_secret_version(request={"name": name})
    _labelbox_api_key = response.payload.data.decode("UTF-8")

SERVICE_SECRET = os.environ.get('SERVICE_SECRET')
if SERVICE_SECRET is None:
    secret_id = f"{_deployment_name}_service_secret"
    name = f"projects/{google_cloud_project}/secrets/{secret_id}/versions/1"
    response = client.access_secret_version(request={"name": name})
    SERVICE_SECRET = response.payload.data.decode("UTF-8")

# This should always be set (set in the build arg)
_gcs_bucket = os.environ['GCS_BUCKET']

# Uses default project for your credentials. Can overwrite here if necessary.
aiplatform.init(project=google_cloud_project,
                staging_bucket=f"gs://{_gcs_bucket}")


class Pipelines(TypedDict):
    bounding_box: Pipeline
    ner: Pipeline
    image_single_classification: Pipeline
    image_multi_classification: Pipeline
    text_single_classification: Pipeline
    text_multi_classification: Pipeline


_common_params = [
    _deployment_name, _labelbox_api_key, _gcs_bucket, service_account,
    google_cloud_project
]
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
