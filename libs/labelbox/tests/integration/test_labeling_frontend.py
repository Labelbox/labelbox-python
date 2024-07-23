from labelbox import LabelingFrontend
import pytest


def test_get_labeling_frontends(client):
    filtered_frontends = list(
        client.get_labeling_frontends(where=LabelingFrontend.name == 'Editor'))
    assert len(filtered_frontends)


@pytest.mark.skip(
    reason="broken due to get_projects HF for sunset-custom-editor")
def test_labeling_frontend_connecting_to_project(project):
    client = project.client
    default_labeling_frontend = next(
        client.get_labeling_frontends(where=LabelingFrontend.name == "Editor"))

    assert project.labeling_frontend(
    ) == default_labeling_frontend  # we now have a default labeling frontend

    frontend = list(project.client.get_labeling_frontends())[0]
    project.labeling_frontend.connect(frontend)

    project.labeling_frontend.connect(frontend)
    assert project.labeling_frontend() == default_labeling_frontend

    project.labeling_frontend.disconnect(frontend)
    assert project.labeling_frontend() == None
