import json

import pytest

from labelbox import LabelingFrontend
from labelbox.exceptions import NetworkError

def simple_ontology():
    classifications = [{
        "name": "test_ontology",
        "instructions": "Which class is this?",
        "type": "radio",
        "options": [{"value": c, "label": c} for c in ["one", "two", "three"]],
        "required": True,
    }]

    return {"tools": [], "classifications": classifications}

def test_project_setup(client, rand_gen):
    project = client.create_project(name=rand_gen(str))

    # TODO this can only run against the staging server
    labeling_frontends = list(client.get_all(
        LabelingFrontend, where=LabelingFrontend.iframe_url_path ==
        "https://staging-image-segmentation-v4.labelbox.com"))
    assert len(labeling_frontends) == 1
    labeling_frontend = labeling_frontends[0]

    project.setup(labeling_frontend, simple_ontology())

    assert project.labeling_frontend() == labeling_frontend
    options = list(project.labeling_frontend_options())
    assert len(options) == 1
    options = options[0]
    # TODO ensure that LabelingFrontendOptions can be obtaind by ID
    with pytest.raises(NetworkError):
        assert options.labeling_frontend() == labeling_frontend
        assert options.project() == project
        assert options.organization() == client.get_organization()
    assert options.customization_options == json.dumps(simple_ontology())

    project.delete()
