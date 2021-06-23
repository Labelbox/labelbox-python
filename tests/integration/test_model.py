from labelbox import Model


def test_model(client, configured_project, rand_gen):
    before = list(client.get_models())
    for m in before:
        assert isinstance(m, Model)

    ontology = configured_project.ontology()

    data = {"name": rand_gen(str), "ontology_id": ontology.uid}
    model = client.create_model(data["name"], data["ontology_id"])
    assert model.name == data["name"]
    assert model.ontology().uid == data["ontology_id"]

    after = list(client.get_models())
    assert len(after) == len(before) + 1
    assert model in after

    model = client.get_model(model.uid)
    assert model.name == data["name"]
    assert model.ontology().uid == data["ontology_id"]
