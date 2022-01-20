from labelbox import Project
from labelbox.data.annotation_types import Rectangle
import random
import json
from google.cloud.storage.blob import Blob
import argparse
import time
import logging
from labelbox import Client
from google.cloud import storage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

supported_extensions = ('JPEG', 'PNG', 'GIF', 'BMP', 'ICO')
#max_file_size = 30MB


def validate_annotations():
    #For each label you must have at least 10 images, each with at least one annotation (bounding box and the label).
    #At least 0.01 * length of a side of an image. For example, a 1000 * 900 pixel image would require bounding boxes of at least 10 * 9 pixels.
    #Bound box minium size: 8 pixels by 8 pixels.

    # If your data is not compatible with these requirements, then the job will fail.
    # A custom workflow will be needed.
    ...


def validate_ontology(ontology):
    # Can only have a single ontology
    ...


def bounding_box_etl(project: Project) -> str:
    ontology = project.ontology()
    validate_ontology(ontology)
    training_data = []
    for label in project.label_generator():
        bounding_box_annotations = []
        for annotation in label.annotations:
            if isinstance(annotation.value, Rectangle):
                bounding_box_annotations.append({
                    "displayName": annotation.name,
                    "xMin": annotation.value.start.x,
                    "yMin": annotation.value.start.y,
                    "xMax": annotation.value.end.x,
                    "yMax": annotation.value.end.y,
                })
        # Note that the gcs uri will require us to re-upload each time..
        training_data.append(
            json.dumps({
                'imageGcsUri': label.data.url,
                'boundingBoxAnnotations': bounding_box_annotations,
                # TODO: Replace with the split from the export in the future.
                'dataItemResourceLabels': {
                    "aiplatform.googleapis.com/ml_use": [
                        'test', 'train', 'validation'
                    ][random.randint(0, 2)]
                }
            }))
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
    json_data = bounding_box_etl(project)
    blob.upload_from_string(json_data)
    logger.info("ETL Complete. URI: %s", f"gs://{bucket.name}/{blob.name}")


if __name__ == '__main__':
    # TODO: We will want to share these for all etl..
    parser = argparse.ArgumentParser(description='Vertex AI ETL Runner')
    parser.add_argument('--gcs_bucket', type=str, required=True)
    parser.add_argument('--project_id', type=str, required=True)
    parser.add_argument('--gcs_key', type=str, required=False, default=None)
    args = parser.parse_args()
    main(**vars(args))
