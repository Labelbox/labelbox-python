import uuid
import ndjson
import pytest

from labelbox.schema.annotation_import import AnnotationImportState, MEAPredictionImport
from labelbox.data.serialization import NDJsonConverter
"""
- Here we only want to check that the uploads are calling the validation
- Then with unit tests we can check the types of errors raised

"""


def test_create_from_url(model_run_with_model_run_data_rows,
                         annotation_import_test_helpers):
    name = str(uuid.uuid4())
    url = "https://storage.googleapis.com/labelbox-public-bucket/predictions_test_v2.ndjson"
    annotation_import = model_run_with_model_run_data_rows.add_predictions(
        name=name, predictions=url)
    assert annotation_import.model_run_id == model_run_with_model_run_data_rows.uid
    annotation_import_test_helpers.check_running_state(annotation_import, name,
                                                       url)
    annotation_import.wait_until_done()


def test_create_from_objects(model_run_with_model_run_data_rows,
                             object_predictions,
                             annotation_import_test_helpers):
    name = str(uuid.uuid4())

    annotation_import = model_run_with_model_run_data_rows.add_predictions(
        name=name, predictions=object_predictions)

    assert annotation_import.model_run_id == model_run_with_model_run_data_rows.uid
    annotation_import_test_helpers.check_running_state(annotation_import, name)
    annotation_import_test_helpers.assert_file_content(
        annotation_import.input_file_url, object_predictions)
    annotation_import.wait_until_done()


def test_create_from_label_objects(model_run_with_model_run_data_rows,
                                   object_predictions,
                                   annotation_import_test_helpers):
    name = str(uuid.uuid4())

    predictions = list(NDJsonConverter.deserialize(object_predictions))

    annotation_import = model_run_with_model_run_data_rows.add_predictions(
        name=name, predictions=predictions)

    assert annotation_import.model_run_id == model_run_with_model_run_data_rows.uid
    annotation_import_test_helpers.check_running_state(annotation_import, name)
    normalized_predictions = NDJsonConverter.serialize(predictions)
    annotation_import_test_helpers.assert_file_content(
        annotation_import.input_file_url, normalized_predictions)
    annotation_import.wait_until_done()


def test_create_from_local_file(tmp_path, model_run_with_model_run_data_rows,
                                object_predictions,
                                annotation_import_test_helpers):
    name = str(uuid.uuid4())
    file_name = f"{name}.ndjson"
    file_path = tmp_path / file_name
    with file_path.open("w") as f:
        ndjson.dump(object_predictions, f)

    annotation_import = model_run_with_model_run_data_rows.add_predictions(
        name=name, predictions=str(file_path))

    assert annotation_import.model_run_id == model_run_with_model_run_data_rows.uid
    annotation_import_test_helpers.check_running_state(annotation_import, name)
    annotation_import_test_helpers.assert_file_content(
        annotation_import.input_file_url, object_predictions)
    annotation_import.wait_until_done()


def test_get(client, model_run_with_model_run_data_rows,
             annotation_import_test_helpers):
    name = str(uuid.uuid4())
    url = "https://storage.googleapis.com/labelbox-public-bucket/predictions_test_v2.ndjson"
    model_run_with_model_run_data_rows.add_predictions(name=name,
                                                       predictions=url)

    annotation_import = MEAPredictionImport.from_name(
        client, model_run_id=model_run_with_model_run_data_rows.uid, name=name)

    assert annotation_import.model_run_id == model_run_with_model_run_data_rows.uid
    annotation_import_test_helpers.check_running_state(annotation_import, name,
                                                       url)
    annotation_import.wait_until_done()


@pytest.mark.slow
def test_wait_till_done(model_run_predictions,
                        model_run_with_model_run_data_rows):
    name = str(uuid.uuid4())
    annotation_import = model_run_with_model_run_data_rows.add_predictions(
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
