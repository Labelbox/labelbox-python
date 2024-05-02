import pytest

def test_add_single_model_config(configured_project, model_config):
    project_model_config_id = configured_project.add_model_config(model_config.uid)

    assert set(config.uid for config in configured_project.project_model_configs()) == set([project_model_config_id])

    assert configured_project.delete_project_model_config(project_model_config_id)


def test_add_multiple_model_config(client, rand_gen, configured_project, model_config, valid_model_id):
    second_model_config = client.create_model_config(rand_gen(str), valid_model_id, {"param": "value"})
    first_project_model_config_id = configured_project.add_model_config(model_config.uid)
    second_project_model_config_id = configured_project.add_model_config(second_model_config.uid)
    expected_model_configs = set([first_project_model_config_id, second_project_model_config_id])

    assert set(config.uid for config in configured_project.project_model_configs()) == expected_model_configs

    for project_model_config_id in expected_model_configs:
        assert configured_project.delete_project_model_config(project_model_config_id)


def test_delete_project_model_config(configured_project, model_config):
    assert configured_project.delete_project_model_config(configured_project.add_model_config(model_config.uid))
    assert not len(configured_project.project_model_configs())
