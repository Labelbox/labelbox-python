import time
import os
import pytest

from collections import Counter

from labelbox import DataSplit, ModelRun


@pytest.fixture
def current_model(client, configured_project_with_label, rand_gen):
    project, _, _, label = configured_project_with_label
    ontology = project.ontology()

    model = client.create_model(rand_gen(str), ontology.uid)
    yield model

    model.delete()


def test_model_run(
    client, configured_project_with_label, current_model, data_row, rand_gen
):
    _, _, _, label = configured_project_with_label
    label_id = label.uid
    model = current_model

    name = rand_gen(str)
    config = {"batch_size": 100, "reruns": None}
    model_run = model.create_model_run(name, config)
    assert model_run.name == name
    assert model_run.training_metadata["batchSize"] == config["batch_size"]
    assert model_run.training_metadata["reruns"] == config["reruns"]
    assert model_run.model_id == model.uid
    assert model_run.created_by_id == client.get_user().uid

    model_run.upsert_labels([label_id])
    time.sleep(3)

    model_run_data_row = next(model_run.model_run_data_rows())
    assert model_run_data_row.label_id == label_id
    assert model_run_data_row.model_run_id == model_run.uid
    assert model_run_data_row.data_row().uid == data_row.uid

    fetch_model_run = client.get_model_run(model_run.uid)
    assert fetch_model_run == model_run


def test_model_run_no_config(rand_gen, model):
    name = rand_gen(str)
    model_run = model.create_model_run(name)
    assert model_run.name == name


def test_model_run_delete(client, model_run):
    models_before = list(client.get_models())
    model_before = models_before[0]
    before = list(model_before.model_runs())

    model_run = before[0]
    model_run.delete()

    models_after = list(client.get_models())
    model_after = models_after[0]
    after = list(model_after.model_runs())
    after_uids = {mr.uid for mr in after}

    assert model_run.uid not in after_uids


def test_model_run_update_config(model_run_with_training_metadata):
    new_config = {"batch_size": 2000}
    res = model_run_with_training_metadata.update_config(new_config)
    assert res["trainingMetadata"]["batch_size"] == new_config["batch_size"]


def test_model_run_reset_config(model_run_with_training_metadata):
    res = model_run_with_training_metadata.reset_config()
    assert res["trainingMetadata"] is None


def test_model_run_get_config(model_run_with_training_metadata):
    new_config = {"batch_size": 2000}
    model_run_with_training_metadata.update_config(new_config)
    res = model_run_with_training_metadata.get_config()
    assert res["batch_size"] == new_config["batch_size"]


def test_model_run_data_rows_delete(model_run_with_data_rows):
    model_run = model_run_with_data_rows

    before = list(model_run.model_run_data_rows())
    annotation_data_row = before[0]

    data_row_id = annotation_data_row.data_row().uid
    model_run.delete_model_run_data_rows(data_row_ids=[data_row_id])
    after = list(model_run.model_run_data_rows())
    assert len(before) == len(after) + 1


def test_model_run_upsert_data_rows(dataset, model_run, configured_project):
    n_model_run_data_rows = len(list(model_run.model_run_data_rows()))
    assert n_model_run_data_rows == 0
    data_row = dataset.create_data_row(row_data="test row data")
    configured_project._wait_until_data_rows_are_processed(
        data_row_ids=[data_row.uid]
    )
    model_run.upsert_data_rows([data_row.uid])
    n_model_run_data_rows = len(list(model_run.model_run_data_rows()))
    assert n_model_run_data_rows == 1


@pytest.mark.parametrize("data_rows", [2], indirect=True)
def test_model_run_upsert_data_rows_using_global_keys(model_run, data_rows):
    global_keys = [dr.global_key for dr in data_rows]
    assert model_run.upsert_data_rows(global_keys=global_keys)
    model_run_data_rows = list(model_run.model_run_data_rows())
    added_data_rows = [mdr.data_row() for mdr in model_run_data_rows]
    assert set(added_data_rows) == set(data_rows)


def test_model_run_upsert_data_rows_with_existing_labels(
    model_run_with_data_rows,
):
    model_run_data_rows = list(model_run_with_data_rows.model_run_data_rows())
    n_data_rows = len(model_run_data_rows)
    model_run_with_data_rows.upsert_data_rows(
        [
            model_run_data_row.data_row().uid
            for model_run_data_row in model_run_data_rows
        ]
    )
    assert n_data_rows == len(
        list(model_run_with_data_rows.model_run_data_rows())
    )


@pytest.mark.skipif(
    condition=os.environ["LABELBOX_TEST_ENVIRON"] == "onprem",
    reason="does not work for onprem",
)
def test_model_run_status(model_run_with_data_rows):
    def get_model_run_status():
        return model_run_with_data_rows.client.execute(
            """query trainingPipelinePyApi($modelRunId: ID!) {
            trainingPipeline(where: {id : $modelRunId}) {status, errorMessage, metadata}}
        """,
            {"modelRunId": model_run_with_data_rows.uid},
            experimental=True,
        )["trainingPipeline"]

    model_run_status = get_model_run_status()
    assert model_run_status["status"] is None
    assert model_run_status["metadata"] is None
    assert model_run_status["errorMessage"] is None

    status = "COMPLETE"
    metadata = {"key1": "value1"}
    errorMessage = "an error"
    model_run_with_data_rows.update_status(status, metadata, errorMessage)

    model_run_status = get_model_run_status()
    assert model_run_status["status"] == status
    assert model_run_status["metadata"] == metadata
    assert model_run_status["errorMessage"] == errorMessage

    extra_metadata = {"key2": "value2"}
    model_run_with_data_rows.update_status(status, extra_metadata)
    model_run_status = get_model_run_status()
    assert model_run_status["status"] == status
    assert model_run_status["metadata"] == {**metadata, **extra_metadata}
    assert model_run_status["errorMessage"] == errorMessage

    status = ModelRun.Status.FAILED
    model_run_with_data_rows.update_status(status, metadata, errorMessage)
    model_run_status = get_model_run_status()
    assert model_run_status["status"] == status.value

    with pytest.raises(ValueError):
        model_run_with_data_rows.update_status(
            "INVALID", metadata, errorMessage
        )


def test_model_run_split_assignment_by_data_row_ids(
    model_run, dataset, image_url
):
    n_data_rows = 2
    data_rows = dataset.create_data_rows(
        [{"row_data": image_url} for _ in range(n_data_rows)]
    )
    data_rows.wait_till_done()
    data_row_ids = [data_row["id"] for data_row in data_rows.result]
    model_run.upsert_data_rows(data_row_ids)

    with pytest.raises(ValueError):
        model_run.assign_data_rows_to_split(data_row_ids, "INVALID SPLIT")

    for split in ["TRAINING", "TEST", "VALIDATION", "UNASSIGNED", *DataSplit]:
        model_run.assign_data_rows_to_split(data_row_ids, split)
        counts = Counter()
        for data_row in model_run.model_run_data_rows():
            counts[data_row.data_split.value] += 1
        split = split.value if isinstance(split, DataSplit) else split
        assert counts[split] == n_data_rows


@pytest.mark.parametrize("data_rows", [2], indirect=True)
def test_model_run_split_assignment_by_global_keys(model_run, data_rows):
    global_keys = [data_row.global_key for data_row in data_rows]

    model_run.upsert_data_rows(global_keys=global_keys)

    for split in ["TRAINING", "TEST", "VALIDATION", "UNASSIGNED", *DataSplit]:
        model_run.assign_data_rows_to_split(
            split=split, global_keys=global_keys
        )
        splits = [
            data_row.data_split.value
            for data_row in model_run.model_run_data_rows()
        ]
        assert len(set(splits)) == 1
