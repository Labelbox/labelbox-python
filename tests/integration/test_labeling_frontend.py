from labelbox import LabelingFrontend


def test_get_labeling_frontends(client):
    frontends = list(client.get_labeling_frontends())
    assert len(frontends) == 1, frontends

    # Test filtering
    single = list(
        client.get_labeling_frontends(where=LabelingFrontend.iframe_url_path ==
                                      frontends[0].iframe_url_path))
    assert len(single) == 1, single


def test_labeling_frontend_connecting_to_project(project):
    assert project.labeling_frontend() == None

    frontend = list(project.client.get_labeling_frontends())[0]

    project.labeling_frontend.connect(frontend)
    assert project.labeling_frontend() == frontend
    assert project in set(frontend.projects())

    project.labeling_frontend.disconnect(frontend)
    assert project.labeling_frontend() == None
    assert project not in set(frontend.projects())
