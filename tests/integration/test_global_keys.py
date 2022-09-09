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
    client.assign_global_keys_to_data_rows(assignment_inputs)

    res = client.get_data_row_ids_for_global_keys([gk_1, gk_2])

    assert len(res['results']) == 2
    successful_assignments = set(res['results'])
    assert successful_assignments == row_ids


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
    assert e in str(excinfo.value)