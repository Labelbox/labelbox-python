import pytest


def test_create_offline_chat_evaluation_project(
    client,
    rand_gen,
    offline_chat_evaluation_project,
    chat_evaluation_ontology,
    offline_conversational_data_row,
    model_config,
):
    project = offline_chat_evaluation_project
    assert project

    ontology = chat_evaluation_ontology
    project.connect_ontology(ontology)

    assert project.labeling_frontend().name == "Editor"
    assert project.ontology().name == ontology.name

    batch = project.create_batch(
        rand_gen(str),
        [offline_conversational_data_row.uid],  # sample of data row objects
    )
    assert batch

    # Can not add a model config to an offline chat evaluation project, since we do not use live models
    with pytest.raises(Exception):
        project.add_model_config(model_config.uid)
