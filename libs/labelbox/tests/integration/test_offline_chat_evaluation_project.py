def test_create_offline_chat_evaluation_project(client,
                                                offline_chat_evaluation_project,
                                                chat_evaluation_ontology):
    project = offline_chat_evaluation_project
    assert project

    ontology = chat_evaluation_ontology
    project.setup_editor(ontology)

    assert project.labeling_frontend().name == "Editor"
    assert project.ontology().name == ontology.name
