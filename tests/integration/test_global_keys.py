from tkinter import E
import uuid
import pytest


def test_assign_global_keys_to_data_rows(client, dataset, image_url):
    """Test that the assign_global_keys_to_data_rows method can be called
    with a valid list of AssignGlobalKeyToDataRowInput objects.
    """

    dr_1 = dataset.create_data_row(row_data=image_url, external_id="hello")
    dr_2 = dataset.create_data_row(row_data=image_url, external_id="world")
    row_ids = set([dr_1.uid, dr_2.uid])

    gk_1 = str(uuid.uuid4())
    gk_2 = str(uuid.uuid4())

    assignment_inputs = [{
        "data_row_id": dr_1.uid,
        "global_key": gk_1
    }, {
        "data_row_id": dr_2.uid,
        "global_key": gk_2
    }]
    res = client.assign_global_keys_to_data_rows(assignment_inputs)
    assert res['status'] == "SUCCESS"
    assert res['errors'] == []

    assert len(res['results']) == 2
    for r in res['results']:
        del r['sanitized']
    assert res['results'] == assignment_inputs


def test_assign_global_keys_to_data_rows_validation_error(client):
    assignment_inputs = [{
        "data_row_id": "test uid",
        "wrong_key": "gk 1"
    }, {
        "data_row_id": "test uid 2",
        "global_key": "gk 2"
    }, {
        "wrong_key": "test uid 3",
        "global_key": "gk 3"
    }, {
        "data_row_id": "test uid 4"
    }, {
        "global_key": "gk 5"
    }, {}]
    with pytest.raises(ValueError) as excinfo:
        client.assign_global_keys_to_data_rows(assignment_inputs)
    e = """[{'data_row_id': 'test uid', 'wrong_key': 'gk 1'}, {'wrong_key': 'test uid 3', 'global_key': 'gk 3'}, {'data_row_id': 'test uid 4'}, {'global_key': 'gk 5'}, {}]"""
    assert e


def test_assign_same_global_keys_to_data_rows(client, dataset, image_url):
    dr_1 = dataset.create_data_row(row_data=image_url, external_id="hello")
    dr_2 = dataset.create_data_row(row_data=image_url, external_id="world")

    gk_1 = str(uuid.uuid4())

    assignment_inputs = [{
        "data_row_id": dr_1.uid,
        "global_key": gk_1
    }, {
        "data_row_id": dr_2.uid,
        "global_key": gk_1
    }]
    res = client.assign_global_keys_to_data_rows(assignment_inputs)

    assert res['status'] == "PARTIAL SUCCESS"
    assert len(res['results']) == 1
    assert res['results'][0]['data_row_id'] == dr_1.uid
    assert res['results'][0]['global_key'] == gk_1

    assert len(res['errors']) == 1
    assert res['errors'][0]['data_row_id'] == dr_2.uid
    assert res['errors'][0]['global_key'] == gk_1
    assert res['errors'][0]['error'] == "Invalid global key"
