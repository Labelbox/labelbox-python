def test_enable_model_assisted_labeling(project):
    response = project.enable_model_assisted_labeling()
    assert response == True

    response = project.enable_model_assisted_labeling(True)
    assert response == True

    response = project.enable_model_assisted_labeling(False)
    assert response == False
