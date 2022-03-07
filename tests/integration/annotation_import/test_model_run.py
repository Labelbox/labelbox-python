import time


def test_model_run(client, configured_project_with_label, rand_gen):
    project, _, _, label = configured_project_with_label
    label_id = label.uid
    ontology = project.ontology()
    data = {"name": rand_gen(str), "ontology_id": ontology.uid}
    model = client.create_model(data["name"], data["ontology_id"])

    name = rand_gen(str)
    model_run = model.create_model_run(name)
    assert model_run.name == name
    assert model_run.model_id == model.uid
    assert model_run.created_by_id == client.get_user().uid

    model_run.upsert_labels([label_id])
    time.sleep(3)

    model_run_data_row = next(model_run.model_run_data_rows())
    assert model_run_data_row.label_id == label_id
    assert model_run_data_row.model_run_id == model_run.uid
    assert model_run_data_row.data_row().uid == next(
        next(project.datasets()).data_rows()).uid

    fetch_model = client.get_model_run(model_run.uid)
    assert fetch_model == model_run


def test_model_run_delete(client, model_run):
    models_before = list(client.get_models())
    model_before = models_before[0]
    before = list(model_before.model_runs())

    model_run = before[0]
    model_run.delete()

    models_after = list(client.get_models())
    model_after = models_after[0]
    after = list(model_after.model_runs())

    assert len(before) == len(after) + 1


def test_model_run_data_rows_delete(client, model_run_with_model_run_data_rows):
    models = list(client.get_models())
    model = models[0]
    model_runs = list(model.model_runs())
    model_run = model_runs[0]

    before = list(model_run.model_run_data_rows())
    annotation_data_row = before[0]

    data_row_id = annotation_data_row.data_row().uid
    model_run.delete_model_run_data_rows(data_row_ids=[data_row_id])
    after = list(model_run.model_run_data_rows())
    assert len(before) == len(after) + 1


def test_model_run_upsert_data_rows(dataset, model_run):
    n_model_run_data_rows = len(list(model_run.model_run_data_rows()))
    assert n_model_run_data_rows == 0
    data_row = dataset.create_data_row(row_data="test row data")
    model_run.upsert_data_rows([data_row.uid])
    n_model_run_data_rows = len(list(model_run.model_run_data_rows()))
    assert n_model_run_data_rows == 1


def test_model_run_upsert_data_rows_with_existing_labels(
        model_run_with_model_run_data_rows):
    model_run_data_rows = list(
        model_run_with_model_run_data_rows.model_run_data_rows())
    n_data_rows = len(model_run_data_rows)
    model_run_with_model_run_data_rows.upsert_data_rows([
        model_run_data_row.data_row().uid
        for model_run_data_row in model_run_data_rows
    ])
    assert n_data_rows == len(
        list(model_run_with_model_run_data_rows.model_run_data_rows()))


def test_model_run_export_labels(model_run_with_model_run_data_rows):
    labels = model_run_with_model_run_data_rows.export_labels(download=True)
    assert len(labels) == 3
