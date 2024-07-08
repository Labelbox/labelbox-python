from datetime import datetime, timedelta, timezone
import json
import time

import pytest

from labelbox import LabelingFrontend
from labelbox.exceptions import InvalidQueryError, ResourceConflict


def simple_ontology():
    classifications = [{
        "name": "test_ontology",
        "instructions": "Which class is this?",
        "type": "radio",
        "options": [{
            "value": c,
            "label": c
        } for c in ["one", "two", "three"]],
        "required": True,
    }]

    return {"tools": [], "classifications": classifications}


def test_project_setup(project) -> None:
    client = project.client
    labeling_frontends = list(
        client.get_labeling_frontends(where=LabelingFrontend.name == 'Editor'))
    assert len(labeling_frontends)
    labeling_frontend = labeling_frontends[0]

    time.sleep(3)
    now = datetime.now().astimezone(timezone.utc)

    project.setup(labeling_frontend, simple_ontology())
    assert now - project.setup_complete <= timedelta(seconds=3)
    assert now - project.last_activity_time <= timedelta(seconds=3)

    assert project.labeling_frontend() == labeling_frontend
    options = list(project.labeling_frontend_options())
    assert len(options) == 1
    options = options[0]
    # TODO ensure that LabelingFrontendOptions can be obtaind by ID
    with pytest.raises(InvalidQueryError):
        assert options.labeling_frontend() == labeling_frontend
        assert options.project() == project
        assert options.organization() == client.get_organization()
    assert options.customization_options == json.dumps(simple_ontology())
    assert project.organization() == client.get_organization()
    assert project.created_by() == client.get_user()


def test_project_editor_setup(client, project, rand_gen):
    ontology_name = f"test_project_editor_setup_ontology_name-{rand_gen(str)}"
    ontology = client.create_ontology(ontology_name, simple_ontology())
    now = datetime.now().astimezone(timezone.utc)
    project.connect_ontology(ontology)
    assert now - project.setup_complete <= timedelta(seconds=3)
    assert now - project.last_activity_time <= timedelta(seconds=3)
    assert project.labeling_frontend().name == "Editor"
    assert project.organization() == client.get_organization()
    assert project.created_by() == client.get_user()
    assert project.ontology().name == ontology_name
    # Make sure that setup only creates one ontology
    time.sleep(3)  # Search takes a second
    assert [ontology.name for ontology in client.get_ontologies(ontology_name)
           ] == [ontology_name]


def test_project_connect_ontology_cant_call_multiple_times(
        client, project, rand_gen):
    ontology_name = f"test_project_editor_setup_ontology_name-{rand_gen(str)}"
    ontology = client.create_ontology(ontology_name, simple_ontology())
    project.connect_ontology(ontology)
    with pytest.raises(ValueError):
        project.connect_ontology(ontology)
