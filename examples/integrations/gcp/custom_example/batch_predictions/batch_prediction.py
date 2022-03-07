import os
import ndjson
import uuid
from typing import Sequence, Union

from google.cloud import aiplatform
from google.cloud import storage
from google.cloud.storage.bucket import Bucket

from labelbox import Client
from labelbox.schema.ontology import OntologyBuilder
from labelbox.data.annotation_types import (Label, LabelList, ImageData, Radio,
                                            ClassificationAnnotation,
                                            ClassificationAnswer)
from labelbox.data.serialization import NDJsonConverter

lb = Client()

lb_project = lb.get_project('cl0cpoj500spr0z5fb8xz5ls9')
lb_model = lb.get_model('9db99246-3db5-0b73-8c95-09f896027099')
lb_model_run_id = "9db9924b-59b8-0242-c123-3ac3757132f3"
project = os.environ['GOOGLE_PROJECT']
bucket_name = os.environ['GCS_BUCKET']

storage_client = storage.Client()

vertex_model_id = '8502483835173208064'
vertex_model = aiplatform.Model(vertex_model_id)
etl_file = '2022-03-04_18:36:50.jsonl'


def create_batch_prediction_job(
    model_resource_name: str,
    job_display_name: str,
    gcs_source: Union[str, Sequence[str]],
    gcs_destination: str,
    sync: bool = True,
):
    my_model = aiplatform.Model(model_resource_name)

    batch_prediction_job = my_model.batch_predict(
        job_display_name=job_display_name,
        gcs_source=gcs_source,
        gcs_destination_prefix=gcs_destination,
        sync=sync,
    )

    batch_prediction_job.wait()

    print(batch_prediction_job.display_name)
    print(batch_prediction_job.resource_name)
    print(batch_prediction_job.state)
    return batch_prediction_job


def image_classification_batch_prediction(bucket: Bucket):
    """
    Returns jsonl (as a string) in the format Vertex batch predictions want
    """
    etl_blob = bucket.blob('etl/image-single-classification/' + etl_file)
    etl_jsonl = ndjson.loads(etl_blob.download_as_text())
    predict_data = [
        str({
            "content": l['imageGcsUri'],
            "mimeType": "image/jpeg"
        }) for l in etl_jsonl[:10]
    ]

    return "\n".join(predict_data)


bucket = storage_client.get_bucket(bucket_name)
json_data = image_classification_batch_prediction(bucket)
blob = bucket.blob('predictions/predict.jsonl')
blob.upload_from_string(json_data)

dest = 'gs://' + bucket_name + '/predictions'
blob_uri = 'gs://' + bucket_name + '/predictions/predict.jsonl'

job = create_batch_prediction_job(vertex_model_id, 'test_batch', blob_uri, dest)

predictions_out_name = job.output_info.gcs_output_directory + \
                       '/predictions_00001.jsonl'

# This is ugly but I couldn't find a better way to get
# the predictions jsonl address:
predictions_out_name = predictions_out_name.split(bucket_name)[1][1:]

preds_blob = bucket.blob(predictions_out_name)
preds_jsonl = ndjson.loads(preds_blob.download_as_text())

predictions = LabelList()
ontology = OntologyBuilder.from_project(lb_project)

for l in preds_jsonl:
    data_row_id = l['instance']['content'].split('/')[-1].split('.')[0]
    predictions.append(
        Label(data=ImageData(uid=data_row_id),
              annotations=[
                  ClassificationAnnotation(
                      value=Radio(answer=ClassificationAnswer(
                          name=l['prediction']['displayNames'][0])),
                      name=ontology.classifications[0].instructions)
              ]))

predictions.assign_feature_schema_ids(ontology)

for lb_model_run in lb_model.model_runs():
    if lb_model_run.uid == lb_model_run_id:
        break

upload_task = lb_model_run.add_predictions(
    f'mea-import-{uuid.uuid4()}', NDJsonConverter.serialize(predictions))
upload_task.wait_until_done()
