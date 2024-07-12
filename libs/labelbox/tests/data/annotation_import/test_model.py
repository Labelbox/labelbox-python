import pytest

from labelbox import Model
from labelbox.exceptions import ResourceNotFoundError


def test_model(client, configured_project, rand_gen):
    # Get all
    models = list(client.get_models())
    for m in models:
        assert isinstance(m, Model)

    # Create
    ontology = configured_project.ontology()
    data = {"name": rand_gen(str), "ontology_id": ontology.uid}
    model = client.create_model(data["name"], data["ontology_id"])
    assert model.name == data["name"]

    # Get one
    model = client.get_model(model.uid)
    assert model.name == data["name"]

    # Delete
    model.delete()
    with pytest.raises(ResourceNotFoundError):
        client.get_model(model.uid)
