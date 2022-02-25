import random
import json
import ndjson
import argparse
import time
import logging
from typing import Union, Literal
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
import os

import requests
from google.cloud.storage.bucket import Bucket
from google.cloud import storage
from google.cloud import secretmanager

from labelbox.data.annotation_types import Label, Checklist, Radio
from labelbox.data.serialization import LBV1Converter
from labelbox import Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VERTEX_MIN_TRAINING_EXAMPLES = 1

# Optionally set env var for testing
_labelbox_api_key = os.environ.get('LABELBOX_API_KEY')
if _labelbox_api_key is None:
    client = secretmanager.SecretManagerServiceClient()
    secret_id = "labelbox_api_key"
    name = f"projects/{os.environ['GOOGLE_PROJECT']}/secrets/{secret_id}/versions/1"
    response = client.access_secret_version(request={"name": name})
    _labelbox_api_key = response.payload.data.decode("UTF-8")


def upload_to_gcs(image_url: str, data_row_uid: str, bucket: Bucket) -> str:
    # Vertex will not work unless the input data is a gcs_uri
    image_bytes = BytesIO(requests.get(image_url).content)
    gcs_key = f"training/images/{data_row_uid}.jpg"
    blob = bucket.blob(gcs_key)
    blob.upload_from_file(image_bytes, content_type="image/jpg")
    return f"gs://{bucket.name}/{blob.name}"


def process_single_classification_label(label: Label, bucket: Bucket) -> str:
    classifications = []
    gcs_uri = upload_to_gcs(label.data.url, label.data.uid, bucket)

    for annotation in label.annotations:
        if isinstance(annotation.value, Radio):

            classifications.append(
                {"displayName": annotation.value.answer.name})

    if len(classifications) > 1:
        logger.info(
            "Skipping example. Must provide <= 1 classification per image.")
        return
    elif len(classifications) == 0:
        classification = {'displayName': 'no_label'}
    else:
        classification = classifications[0]
    return json.dumps({
        'imageGcsUri': gcs_uri,
        'classificationAnnotation': classification,
        # TODO: Replace with the split from the export in the future.
        'dataItemResourceLabels': {
            "aiplatform.googleapis.com/ml_use": ['test', 'train', 'validation']
                                                [random.randint(0, 2)]
        }
    })


def process_multi_classification_label(label: Label, bucket: Bucket) -> str:
    classifications = []
    gcs_uri = upload_to_gcs(label.data.url, label.data.uid, bucket)

    for annotation in label.annotations:
        if isinstance(annotation.value, Radio):
            classifications.append(
                {"displayName": annotation.value.answer.name})
        elif isinstance(annotation.value, Checklist):
            classifications.extend([{
                "displayName": answer.name
            } for answer in annotation.value.answer])

    if len(classifications) == 0:
        classifications = [{'displayName': 'no_label'}]

    return json.dumps({
        'imageGcsUri': gcs_uri,
        'classificationAnnotations': classifications,
        # TODO: Replace with the split from the export in the future.
        'dataItemResourceLabels': {
            "aiplatform.googleapis.com/ml_use": ['test', 'train', 'validation']
                                                [random.randint(0, 2)]
        }
    })


def image_classification_etl(lb_client: Client, model_run_id: str,
                             bucket: Bucket, multi: bool) -> str:
    """
    Creates a jsonl file that is used for input into a vertex ai training job

    Read more about the configuration here::
        - Multi: https://cloud.google.com/vertex-ai/docs/datasets/prepare-image#multi-label-classification
        - Single: https://cloud.google.com/vertex-ai/docs/datasets/prepare-image#single-label-classification
    """
    # json_labels = project.export_labels(download=True)
    query_str = """
        mutation exportModelRunAnnotationsPyApi($modelRunId: ID!) {
            exportModelRunAnnotations(data: {modelRunId: $modelRunId}) {
                downloadUrl createdAt status
            }
        }
        """
    url = lb_client.execute(query_str,
                            {'modelRunId': model_run_id
                            })['exportModelRunAnnotations']['downloadUrl']
    counter = 1
    while url is None:
        logger.info(f"Number of times tried: {counter}")
        counter += 1
        if counter > 10:
            raise Exception(
                f"Unsuccessfully got downloadUrl after {counter} attempts.")
        time.sleep(10)
        url = lb_client.execute(query_str,
                                {'modelRunId': model_run_id
                                })['exportModelRunAnnotations']['downloadUrl']

    response = requests.get(url)
    response.raise_for_status()
    contents = ndjson.loads(response.content)

    for row in contents:
        row['media_type'] = 'image'

    labels = LBV1Converter.deserialize(contents)

    fn = process_multi_classification_label if multi else process_single_classification_label
    with ThreadPoolExecutor(max_workers=8) as exc:
        training_data_futures = [
            exc.submit(fn, label, bucket) for label in labels
        ]
        training_data = [future.result() for future in training_data_futures]

    # The requirement seems to only apply to training data.
    # This should be changed to check by split
    if len(training_data) < VERTEX_MIN_TRAINING_EXAMPLES:
        raise Exception("Not enought training examples provided")

    # jsonl
    return "\n".join(training_data)


def main(model_run_id: str, gcs_bucket: str, gcs_key: str,
         classification_type: Union[Literal['single'], Literal['multi']]):
    gcs_client = storage.Client(project=os.environ['GOOGLE_PROJECT'])
    lb_client = Client(api_key=_labelbox_api_key,
                       endpoint='https://api.labelbox.com/_gql')
    bucket = gcs_client.bucket(gcs_bucket)
    nowgmt = time.strftime("%Y-%m-%d_%H:%M:%S", time.gmtime())
    gcs_key = gcs_key or f'etl/{classification_type}-classification/{nowgmt}.jsonl'
    blob = bucket.blob(gcs_key)
    # project = lb_client.get_project(project_id)
    json_data = image_classification_etl(lb_client, model_run_id, bucket,
                                         classification_type == 'multi')
    blob.upload_from_string(json_data)
    logger.info("ETL Complete. URI: %s", f"gs://{bucket.name}/{blob.name}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Vertex AI ETL Runner')
    parser.add_argument('--gcs_bucket', type=str, required=True)
    parser.add_argument('--model_run_id', type=str, required=True)
    parser.add_argument('--classification_type',
                        choices=['single', 'multi'],
                        required=True)
    parser.add_argument('--gcs_key', type=str, required=False, default=None)
    args = parser.parse_args()
    main(**vars(args))
