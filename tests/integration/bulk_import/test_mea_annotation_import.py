import uuid
import ndjson
import pytest
import requests

from labelbox.schema.annotation_import import AnnotationImportState, MEAPredictionImport
"""
- Here we only want to check that the uploads are calling the validation
- Then with unit tests we can check the types of errors raised

"""


def check_running_state(req, name, url=None):
    assert req.name == name
    if url is not None:
        assert req.input_file_url == url
    assert req.error_file_url is None
    assert req.status_file_url is None
    assert req.state == AnnotationImportState.RUNNING


def test_create_from_url(model_run):
    name = str(uuid.uuid4())
    url = "https://storage.googleapis.com/labelbox-public-bucket/predictions_test_v2.ndjson"
    annotation_import = model_run.add_predictions(name=name, predictions=url)
    assert annotation_import.model_run_id == model_run.uid
    check_running_state(annotation_import, name, url)


def test_create_from_objects(model_run, object_predictions):
    name = str(uuid.uuid4())

    annotation_import = model_run.add_predictions(
        name=name, predictions=object_predictions)

    assert annotation_import.model_run_id == model_run.uid
    check_running_state(annotation_import, name)
    assert_file_content(annotation_import.input_file_url, object_predictions)


def test_create_from_local_file(tmp_path, model_run, object_predictions):
    name = str(uuid.uuid4())
    file_name = f"{name}.ndjson"
    file_path = tmp_path / file_name
    with file_path.open("w") as f:
        ndjson.dump(object_predictions, f)

    annotation_import = model_run.add_predictions(name=name,
                                                  predictions=str(file_path))

    assert annotation_import.model_run_id == model_run.uid
    check_running_state(annotation_import, name)
    assert_file_content(annotation_import.input_file_url, object_predictions)


def test_get(client, model_run):
    name = str(uuid.uuid4())
    url = "https://storage.googleapis.com/labelbox-public-bucket/predictions_test_v2.ndjson"
    model_run.add_predictions(name=name, predictions=url)

    annotation_import = MEAPredictionImport.from_name(client,
                                                      parent_id=model_run.uid,
                                                      name=name)

    assert annotation_import.model_run_id == model_run.uid
    check_running_state(annotation_import, name, url)


@pytest.mark.slow
def test_wait_till_done(model_run_predictions, model_run):
    name = str(uuid.uuid4())
    annotation_import = model_run.add_predictions(
        name=name, predictions=model_run_predictions)

    assert len(annotation_import.inputs) == len(model_run_predictions)
    annotation_import.wait_until_done()
    assert annotation_import.state == AnnotationImportState.FINISHED
    # Check that the status files are being returned as expected
    assert len(annotation_import.errors) == 0
    assert len(annotation_import.inputs) == len(model_run_predictions)
    input_uuids = [
        input_annot['uuid'] for input_annot in annotation_import.inputs
    ]
    inference_uuids = [pred['uuid'] for pred in model_run_predictions]
    assert set(input_uuids) == set(inference_uuids)
    assert len(annotation_import.statuses) == len(model_run_predictions)
    for status in annotation_import.statuses:
        assert status['status'] == 'SUCCESS'
    status_uuids = [
        input_annot['uuid'] for input_annot in annotation_import.statuses
    ]
    assert set(input_uuids) == set(status_uuids)


def assert_file_content(url: str, predictions):
    response = requests.get(url)
    assert response.text == ndjson.dumps(predictions)
