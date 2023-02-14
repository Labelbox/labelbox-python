import uuid
import ndjson
import pytest
import random

from labelbox.data.serialization import NDJsonConverter
from labelbox.exceptions import MALValidationError, UuidError
from labelbox.schema.bulk_import_request import BulkImportRequest
from labelbox.schema.enums import BulkImportRequestState
from labelbox.schema.annotation_import import MALPredictionImport
"""
- Here we only want to check that the uploads are calling the validation
- Then with unit tests we can check the types of errors raised

"""


def test_create_from_url(configured_project):
    name = str(uuid.uuid4())
    url = "https://storage.googleapis.com/labelbox-public-bucket/predictions_test_v2.ndjson"

    bulk_import_request = configured_project.upload_annotations(name=name,
                                                                annotations=url,
                                                                validate=False)

    assert bulk_import_request.project() == configured_project
    assert bulk_import_request.name == name
    assert bulk_import_request.input_file_url == url
    assert bulk_import_request.error_file_url is None
    assert bulk_import_request.status_file_url is None
    assert bulk_import_request.state == BulkImportRequestState.RUNNING


def test_validate_file(configured_project):
    name = str(uuid.uuid4())
    url = "https://storage.googleapis.com/labelbox-public-bucket/predictions_test_v2.ndjson"
    with pytest.raises(MALValidationError):
        configured_project.upload_annotations(name=name,
                                              annotations=url,
                                              validate=True)
        #Schema ids shouldn't match


def test_create_from_objects(configured_project, predictions,
                             annotation_import_test_helpers):
    name = str(uuid.uuid4())

    bulk_import_request = configured_project.upload_annotations(
        name=name, annotations=predictions)

    assert bulk_import_request.project() == configured_project
    assert bulk_import_request.name == name
    assert bulk_import_request.error_file_url is None
    assert bulk_import_request.status_file_url is None
    assert bulk_import_request.state == BulkImportRequestState.RUNNING
    annotation_import_test_helpers.assert_file_content(
        bulk_import_request.input_file_url, predictions)


def test_create_from_label_objects(configured_project, predictions,
                                   annotation_import_test_helpers):
    name = str(uuid.uuid4())

    labels = list(NDJsonConverter.deserialize(predictions))
    bulk_import_request = configured_project.upload_annotations(
        name=name, annotations=labels)

    assert bulk_import_request.project() == configured_project
    assert bulk_import_request.name == name
    assert bulk_import_request.error_file_url is None
    assert bulk_import_request.status_file_url is None
    assert bulk_import_request.state == BulkImportRequestState.RUNNING
    normalized_predictions = list(NDJsonConverter.serialize(labels))
    annotation_import_test_helpers.assert_file_content(
        bulk_import_request.input_file_url, normalized_predictions)


def test_create_from_local_file(tmp_path, predictions, configured_project,
                                annotation_import_test_helpers):
    name = str(uuid.uuid4())
    file_name = f"{name}.ndjson"
    file_path = tmp_path / file_name
    with file_path.open("w") as f:
        ndjson.dump(predictions, f)

    bulk_import_request = configured_project.upload_annotations(
        name=name, annotations=str(file_path), validate=False)

    assert bulk_import_request.project() == configured_project
    assert bulk_import_request.name == name
    assert bulk_import_request.error_file_url is None
    assert bulk_import_request.status_file_url is None
    assert bulk_import_request.state == BulkImportRequestState.RUNNING
    annotation_import_test_helpers.assert_file_content(
        bulk_import_request.input_file_url, predictions)


def test_get(client, configured_project):
    name = str(uuid.uuid4())
    url = "https://storage.googleapis.com/labelbox-public-bucket/predictions_test_v2.ndjson"
    configured_project.upload_annotations(name=name,
                                          annotations=url,
                                          validate=False)

    bulk_import_request = BulkImportRequest.from_name(
        client, project_id=configured_project.uid, name=name)

    assert bulk_import_request.project() == configured_project
    assert bulk_import_request.name == name
    assert bulk_import_request.input_file_url == url
    assert bulk_import_request.error_file_url is None
    assert bulk_import_request.status_file_url is None
    assert bulk_import_request.state == BulkImportRequestState.RUNNING


def test_validate_ndjson(tmp_path, configured_project):
    file_name = f"broken.ndjson"
    file_path = tmp_path / file_name
    with file_path.open("w") as f:
        f.write("test")

    with pytest.raises(ValueError):
        configured_project.upload_annotations(name="name",
                                              validate=True,
                                              annotations=str(file_path))


def test_validate_ndjson_uuid(tmp_path, configured_project, predictions):
    file_name = f"repeat_uuid.ndjson"
    file_path = tmp_path / file_name
    repeat_uuid = predictions.copy()
    uid = str(uuid.uuid4())
    repeat_uuid[0]['uuid'] = uid
    repeat_uuid[1]['uuid'] = uid

    with file_path.open("w") as f:
        ndjson.dump(repeat_uuid, f)

    with pytest.raises(UuidError):
        configured_project.upload_annotations(name="name",
                                              validate=True,
                                              annotations=str(file_path))

    with pytest.raises(UuidError):
        configured_project.upload_annotations(name="name",
                                              validate=True,
                                              annotations=repeat_uuid)


@pytest.mark.slow
def test_wait_till_done(rectangle_inference, configured_project):
    name = str(uuid.uuid4())
    url = configured_project.client.upload_data(content=ndjson.dumps(
        [rectangle_inference]),
                                                sign=True)
    bulk_import_request = configured_project.upload_annotations(name=name,
                                                                annotations=url,
                                                                validate=False)

    assert len(bulk_import_request.inputs) == 1
    bulk_import_request.wait_until_done()
    assert bulk_import_request.state == BulkImportRequestState.FINISHED

    # Check that the status files are being returned as expected
    assert len(bulk_import_request.errors) == 0
    assert len(bulk_import_request.inputs) == 1
    assert bulk_import_request.inputs[0]['uuid'] == rectangle_inference['uuid']
    assert len(bulk_import_request.statuses) == 1
    assert bulk_import_request.statuses[0]['status'] == 'SUCCESS'
    assert bulk_import_request.statuses[0]['uuid'] == rectangle_inference[
        'uuid']


def test_project_bulk_import_requests(configured_project, predictions):
    result = configured_project.bulk_import_requests()
    assert len(list(result)) == 0

    name = str(uuid.uuid4())
    bulk_import_request = configured_project.upload_annotations(
        name=name, annotations=predictions)
    bulk_import_request.wait_until_done()

    name = str(uuid.uuid4())
    bulk_import_request = configured_project.upload_annotations(
        name=name, annotations=predictions)
    bulk_import_request.wait_until_done()

    name = str(uuid.uuid4())
    bulk_import_request = configured_project.upload_annotations(
        name=name, annotations=predictions)
    bulk_import_request.wait_until_done()

    result = configured_project.bulk_import_requests()
    assert len(list(result)) == 3


def test_delete(configured_project, predictions):
    name = str(uuid.uuid4())

    bulk_import_request = configured_project.upload_annotations(
        name=name, annotations=predictions)
    bulk_import_request.wait_until_done()
    all_import_requests = configured_project.bulk_import_requests()
    assert len(list(all_import_requests)) == 1

    bulk_import_request.delete()
    all_import_requests = configured_project.bulk_import_requests()
    assert len(list(all_import_requests)) == 0


def test_pdf_mal_bbox(client, configured_project_pdf):
    """
    tests pdf mal against only a bbox annotation
    """
    annotations = []
    num_annotations = 1

    for row in configured_project_pdf.export_queued_data_rows():
        for _ in range(num_annotations):
            annotations.append({
                "uuid": str(uuid.uuid4()),
                "name": "bbox",
                "dataRow": {
                    "id": row['id']
                },
                "bbox": {
                    "top": round(random.uniform(0, 300), 2),
                    "left": round(random.uniform(0, 300), 2),
                    "height": round(random.uniform(200, 500), 2),
                    "width": round(random.uniform(0, 200), 2)
                },
                "page": random.randint(0, 1),
                "unit": "POINTS"
            })
        annotations.extend([
            {  #annotations intended to test classifications
                'name': 'text',
                'answer': 'the answer to the text question',
                'uuid': 'fc1913c6-b735-4dea-bd25-c18152a4715f',
                "dataRow": {
                    "id": row['id']
                }
            },
            {
                'name': 'checklist',
                'uuid': '9d7b2e57-d68f-4388-867a-af2a9b233719',
                "dataRow": {
                    "id": row['id']
                },
                'answer': [{
                    'name': 'option1'
                }, {
                    'name': 'optionN'
                }]
            },
            {
                'name': 'radio',
                'answer': {
                    'name': 'second_radio_answer'
                },
                'uuid': 'ad60897f-ea1a-47de-b923-459339764921',
                "dataRow": {
                    "id": row['id']
                }
            },
            {  #adding this with the intention to ensure we allow page: 0 
                "uuid": str(uuid.uuid4()),
                "name": "bbox",
                "dataRow": {
                    "id": row['id']
                },
                "bbox": {
                    "top": round(random.uniform(0, 300), 2),
                    "left": round(random.uniform(0, 300), 2),
                    "height": round(random.uniform(200, 500), 2),
                    "width": round(random.uniform(0, 200), 2)
                },
                "page": 0,
                "unit": "POINTS"
            }
        ])
    import_annotations = MALPredictionImport.create_from_objects(
        client=client,
        project_id=configured_project_pdf.uid,
        name=f"import {str(uuid.uuid4())}",
        predictions=annotations)
    import_annotations.wait_until_done()

    assert import_annotations.errors == []
