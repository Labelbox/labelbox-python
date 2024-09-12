from labelbox.schema.project import Project
import pytest

from labelbox.schema.ontology_kind import OntologyKind


@pytest.mark.parametrize(
    "prompt_response_ontology", [OntologyKind.ResponseCreation], indirect=True
)
def test_create_response_creation_project(
    client,
    rand_gen,
    response_creation_project,
    prompt_response_ontology,
    response_data_row,
):
    project: Project = response_creation_project
    assert project

    ontology = prompt_response_ontology
    project.connect_ontology(ontology)

    assert project.labeling_frontend().name == "Editor"
    assert project.ontology().name == ontology.name

    batch = project.create_batch(
        rand_gen(str),
        [response_data_row.uid],  # sample of data row objects
    )
    assert batch
