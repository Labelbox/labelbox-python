import time


def test_model_run(client, configured_project_with_label, rand_gen):
    project = configured_project_with_label
    ontology = project.ontology()
    data = {"name": rand_gen(str), "ontology_id": ontology.uid}
    model = client.create_model(data["name"], data["ontology_id"])

    name = rand_gen(str)
    model_run = model.create_model_run(name)
    assert model_run.name == name
    assert model_run.model_id == model.uid
    assert model_run.created_by_id == client.get_user().uid

    label = project.export_labels(download=True)[0]
    model_run.upsert_labels([label['ID']])
    time.sleep(3)

    annotation_group = next(model_run.annotation_groups())
    assert annotation_group.label_id == label['ID']
    assert annotation_group.model_run_id == model_run.uid
    assert annotation_group.data_row().uid == next(
        next(project.datasets()).data_rows()).uid
