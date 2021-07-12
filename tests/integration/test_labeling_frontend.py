from labelbox import LabelingFrontend


def test_get_labeling_frontends(client):
    frontends = list(client.get_labeling_frontends())
    assert len(frontends) >= 1, (
        'Projects should have at least one frontend by default.')

    # Test filtering
    target_frontend = frontends[0]
    filtered_frontends = client.get_labeling_frontends(
        where=LabelingFrontend.iframe_url_path ==
        target_frontend.iframe_url_path)
    for frontend in filtered_frontends:
        assert target_frontend == frontend


def test_labeling_frontend_connecting_to_project(project):
    assert project.labeling_frontend() == None

    frontend = list(project.client.get_labeling_frontends())[0]

    project.labeling_frontend.connect(frontend)
    assert project.labeling_frontend() == frontend

    project.labeling_frontend.disconnect(frontend)
    assert project.labeling_frontend() == None
