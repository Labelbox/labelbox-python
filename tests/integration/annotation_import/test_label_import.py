import uuid
import pytest

from labelbox.schema.annotation_import import AnnotationImportState, LabelImport
from labelbox.data.serialization import NDJsonConverter
"""
- Here we only want to check that the uploads are calling the validation
- Then with unit tests we can check the types of errors raised

"""


def test_create_from_url(client, project, annotation_import_test_helpers):
    name = str(uuid.uuid4())
    url = "https://storage.googleapis.com/labelbox-public-bucket/predictions_test_v2.ndjson"
    label_import = LabelImport.create_from_url(client=client,
                                               project_id=project.uid,
                                               name=name,
                                               url=url)
    assert label_import.parent_id == project.uid
    annotation_import_test_helpers.check_running_state(label_import, name, url)


def test_create_from_objects(client, configured_project, object_predictions,
                             annotation_import_test_helpers):
    """this test should check running state only to validate running, not completed"""
    name = str(uuid.uuid4())

    label_import = LabelImport.create_from_objects(
        client=client,
        project_id=configured_project.uid,
        name=name,
        labels=object_predictions)

    assert label_import.parent_id == configured_project.uid
    annotation_import_test_helpers.check_running_state(label_import, name)
    annotation_import_test_helpers.assert_file_content(
        label_import.input_file_url, object_predictions)


def test_create_from_label_objects(client, configured_project,
                                   object_predictions,
                                   annotation_import_test_helpers):
    """this test should check running state only to validate running, not completed"""
    name = str(uuid.uuid4())

    labels = list(NDJsonConverter.deserialize(object_predictions))

    label_import = LabelImport.create_from_objects(
        client=client,
        project_id=configured_project.uid,
        name=name,
        labels=labels)

    assert label_import.parent_id == configured_project.uid
    annotation_import_test_helpers.check_running_state(label_import, name)
    normalized_predictions = NDJsonConverter.serialize(labels)
    annotation_import_test_helpers.assert_file_content(
        label_import.input_file_url, normalized_predictions)


#   TODO: add me when we add this ability
# def test_create_from_local_file(client, tmp_path, project,
#                                 object_predictions, annotation_import_test_helpers):
#     name = str(uuid.uuid4())
#     file_name = f"{name}.ndjson"
#     file_path = tmp_path / file_name
#     with file_path.open("w") as f:
#         ndjson.dump(object_predictions, f)

#     label_import = LabelImport.create_from_url(client=client, project_id=project.uid, name=name, url=str(file_path))

#     assert label_import.parent_id == project.uid
#     annotation_import_test_helpers.check_running_state(label_import, name)
#     annotation_import_test_helpers.assert_file_content(label_import.input_file_url, object_predictions)


def test_get(client, project, annotation_import_test_helpers):
    name = str(uuid.uuid4())
    url = "https://storage.googleapis.com/labelbox-public-bucket/predictions_test_v2.ndjson"

    label_import = LabelImport.create_from_url(client=client,
                                               project_id=project.uid,
                                               name=name,
                                               url=url)

    assert label_import.parent_id == project.uid
    annotation_import_test_helpers.check_running_state(label_import, name, url)


@pytest.mark.slow
def test_wait_till_done(client, configured_project, predictions):
    name = str(uuid.uuid4())
    label_import = LabelImport.create_from_objects(
        client=client,
        project_id=configured_project.uid,
        name=name,
        labels=predictions)

    assert len(label_import.inputs) == len(predictions)
    label_import.wait_until_done()

    assert label_import.state == AnnotationImportState.FINISHED
    assert len(label_import.inputs) == len(predictions)
    input_uuids = [input_annot['uuid'] for input_annot in label_import.inputs]
    inference_uuids = [pred['uuid'] for pred in predictions]
    assert set(input_uuids) == set(inference_uuids)
    assert len(label_import.statuses) == len(predictions)
    status_uuids = [
        input_annot['uuid'] for input_annot in label_import.statuses
    ]
    assert set(input_uuids) == set(status_uuids)
