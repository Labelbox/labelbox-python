from concurrent.futures import ThreadPoolExecutor
import json
import argparse
import time
import logging
from typing import Tuple
from io import BytesIO
import os

import requests
from PIL.Image import Image, open as load_image
from google.cloud.storage.bucket import Bucket
from google.cloud import storage
from google.cloud import secretmanager

from labelbox.data.annotation_types import Label, Rectangle
from labelbox.data.serialization import LBV1Converter
from labelbox import Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Maps from our partition naming convention to google's
partition_mapping = {
    'training': 'train',
    'test': 'test',
    'validation': 'validation'
}

# Optionally set env var for testing
_labelbox_api_key = os.environ.get('LABELBOX_API_KEY')

if _labelbox_api_key is None:
    deployment_name = os.environ['DEPLOYMENT_NAME']
    client = secretmanager.SecretManagerServiceClient()
    secret_id = f"{deployment_name}_labelbox_api_key"
    name = f"projects/{os.environ['GOOGLE_PROJECT']}/secrets/{secret_id}/versions/1"
    response = client.access_secret_version(request={"name": name})
    _labelbox_api_key = response.payload.data.decode("UTF-8")

VERTEX_MIN_BBOX_DIM = 9
VERTEX_MAX_EXAMPLES_PER_IMAGE = 500
VERTEX_MIN_TRAINING_EXAMPLES = 50


def download_image(image_url: str,
                   scale_w: float = 1 / 2.,
                   scale_h: float = 1 / 2.) -> Tuple[Image, Tuple[int, int]]:
    im = load_image(BytesIO(requests.get(image_url).content))
    w, h = im.size
    return im.resize((int(w * scale_w), int(h * scale_h))), (w, h)


def image_to_bytes(im: Image) -> BytesIO:
    im_bytes = BytesIO()
    im.save(im_bytes, format="jpeg")
    im_bytes.seek(0)
    return im_bytes


def upload_to_gcs(image_bytes: BytesIO, data_row_uid: str, h: int, w: int,
                  bucket: Bucket) -> str:
    # Vertex will not work unless the input data is a gcs_uri
    gcs_key = f"training/images/{data_row_uid}_{int(w)}_{int(h)}.jpg"
    blob = bucket.blob(gcs_key)
    blob.upload_from_file(image_bytes, content_type="image/jpg")
    return f"gs://{bucket.name}/{blob.name}"


def process_label(label: Label, bucket: Bucket) -> str:
    data_split = label.extra.get("Data Split")
    if data_split is None:
        logger.warning("No data split assigned. Skipping.")
        return

    bounding_box_annotations = []
    # TODO: Only download if the label has annotations
    # When this is only necessary since we don't have media attributes in the export yet.
    downsample_factor = 2
    image, (w, h) = download_image(label.data.url, 1. / downsample_factor,
                                   1. / downsample_factor)
    image_bytes = image_to_bytes(image)
    gcs_uri = upload_to_gcs(image_bytes, label.data.uid, h, w, bucket)

    for annotation in label.annotations:
        if isinstance(annotation.value, Rectangle):
            bbox = annotation.value
            if (bbox.end.x - bbox.start.x) < (
                    VERTEX_MIN_BBOX_DIM * downsample_factor) or (
                        bbox.end.y - bbox.start.y) < (VERTEX_MIN_BBOX_DIM *
                                                      downsample_factor):
                logger.info(
                    f"continuing. ({bbox.end.x - bbox.start.x}) or ({bbox.end.y - bbox.start.y}) "
                )
                continue

            # If the points are not within the range [0,1] then vertex will filter them out.
            # This often leads to an error at training time with the following message:
            # "Image Object Detection training requires training, validation and test datasets to be non-empty..."
            bounding_box_annotations.append({
                "displayName": annotation.name,
                "xMin": round(bbox.start.x / w, 2),
                "yMin": round(bbox.start.y / h, 2),
                "xMax": round(bbox.end.x / w, 2),
                "yMax": round(bbox.end.y / h, 2),
            })

    if len(bounding_box_annotations) == 0:
        return

    return json.dumps({
        'imageGcsUri':
            gcs_uri,
        'boundingBoxAnnotations':
            bounding_box_annotations[:VERTEX_MAX_EXAMPLES_PER_IMAGE],
        'dataItemResourceLabels': {
            "aiplatform.googleapis.com/ml_use": partition_mapping[data_split],
            "dataRowId": label.data.uid
        }
    })


def bounding_box_etl(lb_client: Client, model_run_id: str, bucket) -> str:
    """
    Creates a jsonl file that is used for input into a vertex ai training job

    This code barely validates the requirements as listed in the vertex documentation.
    Read more about the restrictions here:
        - https://cloud.google.com/vertex-ai/docs/datasets/prepare-image#object-detection
    """
    model_run = client.get_model_run(model_run_id)
    json_labels = model_run.export_labels(download=True)

    with ThreadPoolExecutor(max_workers=8) as exc:
        training_data_futures = [
            exc.submit(process_label, label, bucket)
            for label in LBV1Converter.deserialize(json_labels)
        ]
    training_data = [future.result() for future in training_data_futures]
    training_data = [
        example for example in training_data if example is not None
    ]

    # The requirement seems to only apply to training data.
    # This should be changed to check by split
    if len(training_data) < VERTEX_MIN_TRAINING_EXAMPLES:
        raise Exception("Not enought training examples provided")

    # jsonl
    return "\n".join(training_data)


def main(model_run_id: str, gcs_bucket: str, gcs_key: str):
    gcs_client = storage.Client(project=os.environ['GOOGLE_PROJECT'],
                                enable_experimental=True)
    lb_client = Client(api_key=_labelbox_api_key,
                       endpoint='https://api.labelbox.com/_gql')
    bucket = gcs_client.bucket(gcs_bucket)
    nowgmt = time.strftime("%Y-%m-%d_%H:%M:%S", time.gmtime())
    gcs_key = gcs_key or f'etl/bounding-box/{nowgmt}.jsonl'
    blob = bucket.blob(gcs_key)
    json_data = bounding_box_etl(lb_client, model_run_id, bucket)
    blob.upload_from_string(json_data)
    logger.info("ETL Complete. URI: %s", f"gs://{bucket.name}/{blob.name}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Vertex AI ETL Runner')
    parser.add_argument('--gcs_bucket', type=str, required=True)
    parser.add_argument('--model_run_id', type=str, required=True)
    parser.add_argument('--gcs_key', type=str, required=False, default=None)
    args = parser.parse_args()
    main(**vars(args))
