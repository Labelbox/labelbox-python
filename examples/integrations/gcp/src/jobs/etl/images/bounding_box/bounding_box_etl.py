import random
import json
import argparse
import time
import logging
from io import BytesIO
import requests

from google.cloud import storage

from labelbox import Client
from labelbox import Project
from labelbox.data.annotation_types import Rectangle

from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VERTEX_MIN_BBOX_DIM = 8
VERTEX_MAX_EXAMPLES_PER_IMAGE = 500
# Technically this is 10. But I don't want this to block dev
VERTEX_MIN_TRAINING_EXAMPLES = 1


def upload_to_gcs(row, bucket):
    # if cuid already exists don't upload?
    image_info = row['imageGcsUri']
    image_url = image_info['url']
    ext = image_url.split('.')[
        -1]  # Idk if this is safe. some people don't have extensions..
    if not len(ext):
        ext = 'jpg'
    gcs_key = f"training/images/{image_info['cuid']}.{ext}"
    blob = bucket.blob(gcs_key)
    im_bytes = BytesIO(requests.get(image_url).content)
    blob.upload_from_file(im_bytes, content_type="image/jpg")
    row['imageGcsUri'] = f"gs://{bucket.name}/{blob.name}"
    return json.dumps(row)


def bounding_box_etl(project: Project, bucket) -> str:
    """
    Creates a jsonl file that is used for input into a vertex ai training job

    This code barely validates the requirements as listed in the vertex documentation.
    Read more about the restrictions here:
        - https://cloud.google.com/vertex-ai/docs/datasets/prepare-image#object-detection

    """

    training_data = []
    for label in project.label_generator():
        bounding_box_annotations = []
        for annotation in label.annotations:
            if isinstance(annotation.value, Rectangle):
                bbox = annotation.value
                if (bbox.end.x - bbox.start.x) < VERTEX_MIN_BBOX_DIM or (
                        bbox.end.y - bbox.start.y) < VERTEX_MIN_BBOX_DIM:
                    continue

                bounding_box_annotations.append({
                    "displayName": annotation.name,
                    "xMin": annotation.value.start.x,
                    "yMin": annotation.value.start.y,
                    "xMax": annotation.value.end.x,
                    "yMax": annotation.value.end.y,
                })
        # TODO: This will not work with vertex unless label.data.url is a gcs_uri
        training_data.append({
            'imageGcsUri': {
                'url': label.data.url,
                'cuid': label.data.uid
            },  # GROSS. Fix this..
            'boundingBoxAnnotations':
                bounding_box_annotations[:VERTEX_MAX_EXAMPLES_PER_IMAGE],
            # TODO: Replace with the split from the export in the future.
            'dataItemResourceLabels': {
                "aiplatform.googleapis.com/ml_use": [
                    'test', 'train', 'validation'
                ][random.randint(0, 2)]
            }
        })
    # The requirement seems to only apply to training data.
    # This should be changed to check by split
    if len(training_data) < VERTEX_MIN_TRAINING_EXAMPLES:
        raise Exception("Not enought training examples provided")

    with ThreadPoolExecutor(max_workers=8) as exc:
        training_data_futures = [
            exc.submit(upload_to_gcs, row, bucket) for row in training_data
        ]
        training_data = [future.result() for future in training_data_futures]

    # jsonl
    return "\n".join(training_data)


def main(project_id, gcs_bucket, gcs_key):
    gcs_client = storage.Client()
    lb_client = Client()
    bucket = gcs_client.bucket(gcs_bucket)
    nowgmt = time.strftime("%Y-%m-%d_%H:%M:%S", time.gmtime())
    gcs_key = gcs_key or f'etl/bounding-box/{nowgmt}.jsonl'
    blob = bucket.blob(gcs_key)
    project = lb_client.get_project(project_id)
    json_data = bounding_box_etl(project, bucket)
    blob.upload_from_string(json_data)
    logger.info("ETL Complete. URI: %s", f"gs://{bucket.name}/{blob.name}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Vertex AI ETL Runner')
    parser.add_argument('--gcs_bucket', type=str, required=True)
    parser.add_argument('--project_id', type=str, required=True)
    parser.add_argument('--gcs_key', type=str, required=False, default=None)
    args = parser.parse_args()
    main(**vars(args))
