import uuid

from labelbox import parser
from labelbox.schema.annotation_import import MALPredictionImport

"""
- Here we only want to check that the uploads are calling the validation
- Then with unit tests we can check the types of errors raised

"""


def test_create_with_url_arg(
    client, module_project, annotation_import_test_helpers
):
    name = str(uuid.uuid4())
    url = "https://storage.googleapis.com/labelbox-public-bucket/predictions_test_v2.ndjson"
    label_import = MALPredictionImport.create(
        client=client, id=module_project.uid, name=name, url=url
    )
    assert label_import.parent_id == module_project.uid
    annotation_import_test_helpers.check_running_state(label_import, name, url)


def test_create_with_labels_arg(
    client, module_project, object_predictions, annotation_import_test_helpers
):
    """this test should check running state only to validate running, not completed"""
    name = str(uuid.uuid4())

    label_import = MALPredictionImport.create(
        client=client,
        id=module_project.uid,
        name=name,
        labels=object_predictions,
    )

    assert label_import.parent_id == module_project.uid
    annotation_import_test_helpers.check_running_state(label_import, name)
    annotation_import_test_helpers.assert_file_content(
        label_import.input_file_url, object_predictions
    )


def test_create_with_path_arg(
    client,
    tmp_path,
    configured_project,
    object_predictions,
    annotation_import_test_helpers,
):
    project = configured_project
    name = str(uuid.uuid4())
    file_name = f"{name}.ndjson"
    file_path = tmp_path / file_name
    with file_path.open("w") as f:
        parser.dump(object_predictions, f)

    label_import = MALPredictionImport.create(
        client=client, id=project.uid, name=name, path=str(file_path)
    )

    assert label_import.parent_id == project.uid
    annotation_import_test_helpers.check_running_state(label_import, name)
    annotation_import_test_helpers.assert_file_content(
        label_import.input_file_url, object_predictions
    )
