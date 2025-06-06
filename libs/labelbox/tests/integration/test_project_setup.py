import time
from datetime import datetime, timedelta, timezone

import pytest
from labelbox.schema.media_type import MediaType


def simple_ontology():
    classifications = [
        {
            "name": "test_ontology",
            "instructions": "Which class is this?",
            "type": "radio",
            "options": [
                {"value": c, "label": c} for c in ["one", "two", "three"]
            ],
            "required": True,
        }
    ]

    return {"tools": [], "classifications": classifications}


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
    assert [
        ontology.name for ontology in client.get_ontologies(ontology_name)
    ] == [ontology_name]


def test_project_connect_ontology_multiple_times(client, project, rand_gen):
    """Test that we can connect multiple ontologies in sequence."""
    # Connect first ontology
    ontology_name_1 = (
        f"test_project_connect_ontology_multiple_times_1-{rand_gen(str)}"
    )
    ontology_1 = client.create_ontology(ontology_name_1, simple_ontology())
    project.connect_ontology(ontology_1)
    assert project.ontology().name == ontology_name_1

    # Connect second ontology
    ontology_name_2 = (
        f"test_project_connect_ontology_multiple_times_2-{rand_gen(str)}"
    )
    ontology_2 = client.create_ontology(ontology_name_2, simple_ontology())
    project.connect_ontology(ontology_2)
    assert project.ontology().name == ontology_name_2


def test_project_connect_ontology_with_different_media_types(client, rand_gen):
    """Test connecting ontologies with different media types to a project"""
    # Create a new project with Image media type
    project_name = f"test_project_media_type_{rand_gen(str)}"
    project = client.create_project(
        name=project_name, media_type=MediaType.Image
    )

    try:
        # Create ontologies with different media types
        ontology_1 = client.create_ontology(
            f"test_ontology_1_{rand_gen(str)}",
            simple_ontology(),
            media_type=MediaType.Image,  # Same media type as project
        )

        ontology_2 = client.create_ontology(
            f"test_ontology_2_{rand_gen(str)}",
            simple_ontology(),
            media_type=MediaType.Video,  # Different media type
        )

        # Test connecting ontology with same media type
        project.connect_ontology(ontology_1)
        assert project.ontology().uid == ontology_1.uid

        # Test connecting ontology with different media type
        with pytest.raises(ValueError) as exc_info:
            project.connect_ontology(ontology_2)
        assert "Ontology and project must share the same type" in str(
            exc_info.value
        )
    finally:
        # Clean up
        project.delete()


def test_project_connect_ontology_with_unknown_type(client, project, rand_gen):
    """Test connecting ontology with unknown media type to a project"""
    # Create ontology with unknown media type
    unknown_type_ontology = client.create_ontology(
        f"test_unknown_type_{rand_gen(str)}", simple_ontology()
    )

    # Test connecting ontology with unknown type
    project.connect_ontology(unknown_type_ontology)
    assert project.ontology().uid == unknown_type_ontology.uid
