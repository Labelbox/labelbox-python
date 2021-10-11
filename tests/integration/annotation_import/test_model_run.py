import time


def test_model_run(client, configured_project_with_label, rand_gen):
    project, label_id = configured_project_with_label
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

    annotation_group = next(model_run.annotation_groups())
    assert annotation_group.label_id == label_id
    assert annotation_group.model_run_id == model_run.uid
    assert annotation_group.data_row().uid == next(
        next(project.datasets()).data_rows()).uid


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


def test_model_run_annotation_groups_delete(client,
                                            model_run_annotation_groups):
    models = list(client.get_models())
    model = models[0]
    model_runs = list(model.model_runs())
    model_run = model_runs[0]

    before = list(model_run.annotation_groups())
    annotation_group = before[0]

    data_row_id = annotation_group.data_row().uid
    model_run.delete_annotation_groups(data_row_ids=[data_row_id])

    after = list(model_run.annotation_groups())

    assert len(before) == len(after) + 1
