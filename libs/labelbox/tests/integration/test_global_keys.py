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

    assignment_inputs = [
        {"data_row_id": dr_1.uid, "global_key": gk_1},
        {"data_row_id": dr_2.uid, "global_key": gk_2},
    ]
    res = client.assign_global_keys_to_data_rows(assignment_inputs)
    assert res["status"] == "SUCCESS"
    assert res["errors"] == []

    assert len(res["results"]) == 2
    for r in res["results"]:
        del r["sanitized"]
    assert res["results"] == assignment_inputs


def test_assign_global_keys_to_data_rows_validation_error(client):
    assignment_inputs = [
        {"data_row_id": "test uid", "wrong_key": "gk 1"},
        {"data_row_id": "test uid 2", "global_key": "gk 2"},
        {"wrong_key": "test uid 3", "global_key": "gk 3"},
        {"data_row_id": "test uid 4"},
        {"global_key": "gk 5"},
        {},
    ]
    with pytest.raises(ValueError) as excinfo:
        client.assign_global_keys_to_data_rows(assignment_inputs)
    e = """[{'data_row_id': 'test uid', 'wrong_key': 'gk 1'}, {'wrong_key': 'test uid 3', 'global_key': 'gk 3'}, {'data_row_id': 'test uid 4'}, {'global_key': 'gk 5'}, {}]"""
    assert e in str(excinfo.value)


def test_assign_same_global_keys_to_data_rows(client, dataset, image_url):
    dr_1 = dataset.create_data_row(row_data=image_url, external_id="hello")
    dr_2 = dataset.create_data_row(row_data=image_url, external_id="world")

    gk_1 = str(uuid.uuid4())

    assignment_inputs = [
        {"data_row_id": dr_1.uid, "global_key": gk_1},
        {"data_row_id": dr_2.uid, "global_key": gk_1},
    ]
    res = client.assign_global_keys_to_data_rows(assignment_inputs)

    assert res["status"] == "PARTIAL SUCCESS"
    assert len(res["results"]) == 1
    assert res["results"][0]["data_row_id"] == dr_1.uid
    assert res["results"][0]["global_key"] == gk_1

    assert len(res["errors"]) == 1
    assert res["errors"][0]["data_row_id"] == dr_2.uid
    assert res["errors"][0]["global_key"] == gk_1
    assert (
        res["errors"][0]["error"]
        == "Invalid assignment. Either DataRow does not exist, or globalKey is invalid"
    )


def test_long_global_key_validation(client, dataset, image_url):
    long_global_key = "x" * 201
    dr_1 = dataset.create_data_row(row_data=image_url)
    dr_2 = dataset.create_data_row(row_data=image_url)

    gk_1 = str(uuid.uuid4())
    gk_2 = long_global_key

    assignment_inputs = [
        {"data_row_id": dr_1.uid, "global_key": gk_1},
        {"data_row_id": dr_2.uid, "global_key": gk_2},
    ]
    res = client.assign_global_keys_to_data_rows(assignment_inputs)

    assert len(res["results"]) == 1
    assert len(res["errors"]) == 1
    assert res["status"] == "PARTIAL SUCCESS"
    assert res["results"][0]["data_row_id"] == dr_1.uid
    assert res["results"][0]["global_key"] == gk_1
    assert res["errors"][0]["data_row_id"] == dr_2.uid
    assert res["errors"][0]["global_key"] == gk_2
    assert (
        res["errors"][0]["error"]
        == "Invalid assignment. Either DataRow does not exist, or globalKey is invalid"
    )


def test_global_key_with_whitespaces_validation(client, dataset, image_url):
    data_row_items = [
        {
            "row_data": image_url,
        },
        {
            "row_data": image_url,
        },
        {
            "row_data": image_url,
        },
    ]
    task = dataset.create_data_rows(data_row_items)
    task.wait_till_done()
    assert task.status == "COMPLETE"
    dr_1_uid, dr_2_uid, dr_3_uid = [t["id"] for t in task.result]

    gk_1 = " global key"
    gk_2 = "global  key"
    gk_3 = "global key "

    assignment_inputs = [
        {"data_row_id": dr_1_uid, "global_key": gk_1},
        {"data_row_id": dr_2_uid, "global_key": gk_2},
        {"data_row_id": dr_3_uid, "global_key": gk_3},
    ]
    res = client.assign_global_keys_to_data_rows(assignment_inputs)

    assert len(res["results"]) == 0
    assert len(res["errors"]) == 3
    assert res["status"] == "FAILURE"
    assign_errors_ids = set([e["data_row_id"] for e in res["errors"]])
    assign_errors_gks = set([e["global_key"] for e in res["errors"]])
    assign_errors_msgs = set([e["error"] for e in res["errors"]])
    assert assign_errors_ids == set([dr_1_uid, dr_2_uid, dr_3_uid])
    assert assign_errors_gks == set([gk_1, gk_2, gk_3])
    assert assign_errors_msgs == set(
        [
            "Invalid assignment. Either DataRow does not exist, or globalKey is invalid",
            "Invalid assignment. Either DataRow does not exist, or globalKey is invalid",
            "Invalid assignment. Either DataRow does not exist, or globalKey is invalid",
        ]
    )


def test_get_data_row_ids_for_global_keys(client, dataset, image_url):
    gk_1 = str(uuid.uuid4())
    gk_2 = str(uuid.uuid4())

    dr_1 = dataset.create_data_row(
        row_data=image_url, external_id="hello", global_key=gk_1
    )
    dr_2 = dataset.create_data_row(
        row_data=image_url, external_id="world", global_key=gk_2
    )

    res = client.get_data_row_ids_for_global_keys([gk_1])
    assert res["status"] == "SUCCESS"
    assert res["errors"] == []
    assert res["results"] == [dr_1.uid]

    res = client.get_data_row_ids_for_global_keys([gk_2])
    assert res["status"] == "SUCCESS"
    assert res["errors"] == []
    assert res["results"] == [dr_2.uid]

    res = client.get_data_row_ids_for_global_keys([gk_1, gk_2])
    assert res["status"] == "SUCCESS"
    assert res["errors"] == []
    assert res["results"] == [dr_1.uid, dr_2.uid]


def test_get_data_row_ids_for_invalid_global_keys(client, dataset, image_url):
    gk_1 = str(uuid.uuid4())
    gk_2 = str(uuid.uuid4())

    dr_1 = dataset.create_data_row(row_data=image_url, external_id="hello")
    dr_2 = dataset.create_data_row(
        row_data=image_url, external_id="world", global_key=gk_2
    )

    res = client.get_data_row_ids_for_global_keys([gk_1])
    assert res["status"] == "FAILURE"
    assert len(res["errors"]) == 1
    assert res["errors"][0]["error"] == "Data Row not found"
    assert res["errors"][0]["global_key"] == gk_1

    res = client.get_data_row_ids_for_global_keys([gk_1, gk_2])
    assert res["status"] == "PARTIAL SUCCESS"

    assert len(res["errors"]) == 1
    assert len(res["results"]) == 2

    assert res["errors"][0]["error"] == "Data Row not found"
    assert res["errors"][0]["global_key"] == gk_1

    assert res["results"][0] == ""
    assert res["results"][1] == dr_2.uid
