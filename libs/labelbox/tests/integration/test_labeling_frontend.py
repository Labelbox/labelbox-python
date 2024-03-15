from labelbox import LabelingFrontend


def test_get_labeling_frontends(client):
    filtered_frontends = list(
        client.get_labeling_frontends(where=LabelingFrontend.name == 'Editor'))
    assert len(filtered_frontends)


def test_labeling_frontend_connecting_to_project(project):
    assert project.labeling_frontend() == None

    frontend = list(project.client.get_labeling_frontends())[0]

    project.labeling_frontend.connect(frontend)
    assert project.labeling_frontend() == frontend

    project.labeling_frontend.disconnect(frontend)
    assert project.labeling_frontend() == None
