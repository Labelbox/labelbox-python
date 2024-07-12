import uuid
from labelbox import parser
import pytest
"""
- Here we only want to check that the uploads are calling the validation
- Then with unit tests we can check the types of errors raised

"""


@pytest.mark.skip()
def test_create_from_url(client, tmp_path, object_predictions,
                         model_run_with_data_rows,
                         configured_project,
                         annotation_import_test_helpers):
    name = str(uuid.uuid4())
    file_name = f"{name}.json"
    file_path = tmp_path / file_name

    model_run_data_rows = [
        mrdr.data_row().uid
        for mrdr in model_run_with_data_rows.model_run_data_rows()
    ]
    predictions = [
        p for p in object_predictions
        if p['dataRow']['id'] in model_run_data_rows
    ]
    with file_path.open("w") as f:
        parser.dump(predictions, f)

    # Needs to have data row ids

    with open(file_path, "r") as f:
        url = client.upload_data(content=f.read(),
                                 filename=file_name,
                                 sign=True,
                                 content_type="application/json")

    annotation_import, batch, mal_prediction_import = model_run_with_data_rows.upsert_predictions_and_send_to_project(
        name=name,
        predictions=url,
        project_id=configured_project.uid,
        priority=5)

    assert annotation_import.model_run_id == model_run_with_data_rows.uid
    annotation_import.wait_until_done()
    assert not annotation_import.errors
    assert annotation_import.statuses

    assert batch
    assert batch.project().uid == configured_project.uid

    assert mal_prediction_import
    mal_prediction_import.wait_until_done()

    assert not mal_prediction_import.errors
    assert mal_prediction_import.statuses


@pytest.mark.skip()
def test_create_from_objects(model_run_with_data_rows,
                             configured_project,
                             object_predictions,
                             annotation_import_test_helpers):
    name = str(uuid.uuid4())
    model_run_data_rows = [
        mrdr.data_row().uid
        for mrdr in model_run_with_data_rows.model_run_data_rows()
    ]
    predictions = [
        p for p in object_predictions
        if p['dataRow']['id'] in model_run_data_rows
    ]
    annotation_import, batch, mal_prediction_import = model_run_with_data_rows.upsert_predictions_and_send_to_project(
        name=name,
        predictions=predictions,
        project_id=configured_project.uid,
        priority=5)

    assert annotation_import.model_run_id == model_run_with_data_rows.uid
    annotation_import.wait_until_done()
    assert not annotation_import.errors
    assert annotation_import.statuses

    assert batch
    assert batch.project().uid == configured_project.uid

    assert mal_prediction_import
    mal_prediction_import.wait_until_done()

    assert not mal_prediction_import.errors
    assert mal_prediction_import.statuses


@pytest.mark.skip()
def test_create_from_local_file(tmp_path, model_run_with_data_rows,
                                configured_project_with_one_data_row,
                                object_predictions,
                                annotation_import_test_helpers):

    name = str(uuid.uuid4())
    file_name = f"{name}.ndjson"
    file_path = tmp_path / file_name

    model_run_data_rows = [
        mrdr.data_row().uid
        for mrdr in model_run_with_data_rows.model_run_data_rows()
    ]
    predictions = [
        p for p in object_predictions
        if p['dataRow']['id'] in model_run_data_rows
    ]

    with file_path.open("w") as f:
        parser.dump(predictions, f)

    annotation_import, batch, mal_prediction_import = model_run_with_data_rows.upsert_predictions_and_send_to_project(
        name=name,
        predictions=str(file_path),
        project_id=configured_project_with_one_data_row.uid,
        priority=5)

    assert annotation_import.model_run_id == model_run_with_data_rows.uid
    annotation_import.wait_until_done()
    assert not annotation_import.errors
    assert annotation_import.statuses

    assert batch
    assert batch.project().uid == configured_project_with_one_data_row.uid

    assert mal_prediction_import
    mal_prediction_import.wait_until_done()

    assert not mal_prediction_import.errors
    assert mal_prediction_import.statuses
