import pytest
from labelbox.exceptions import ResourceNotFoundError


def test_create_model_config(client, valid_model_id):
    model_config = client.create_model_config(
        "model_config", valid_model_id, {"param": "value"}
    )
    assert model_config.inference_params["param"] == "value"
    assert model_config.name == "model_config"
    assert model_config.model_id == valid_model_id


def test_delete_model_config(client, valid_model_id):
    model_config_id = client.create_model_config(
        "model_config", valid_model_id, {"param": "value"}
    )
    assert client.delete_model_config(model_config_id.uid)


def test_delete_nonexistant_model_config(client):
    with pytest.raises(ResourceNotFoundError):
        client.delete_model_config("invalid_model_id")
