def test_enable_model_assisted_labeling(project):
    response = project.enable_model_assisted_labeling()
    assert response is True

    response = project.enable_model_assisted_labeling(True)
    assert response is True

    response = project.enable_model_assisted_labeling(False)
    assert response is False
