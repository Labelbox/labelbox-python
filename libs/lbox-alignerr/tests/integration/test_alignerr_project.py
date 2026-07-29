"""Integration tests for AlignerrProject functionality.

These tests interact with the actual Labelbox API to verify AlignerrProject operations.
"""

import re
import uuid

import pytest
from alignerr.alignerr_project import (
    AlignerrProject,
    AlignerrWorkspace,
    PAY_BY_ROLE_REMOVED_MSG,
)
from labelbox.schema.media_type import MediaType


@pytest.fixture
def test_project(client):
    """Create a test project for AlignerrProject testing."""
    project_name = f"Test AlignerrProject {uuid.uuid4()}"
    project = client.create_project(name=project_name, media_type=MediaType.Image)

    yield project

    # Cleanup
    try:
        project.delete()
    except Exception:
        pass  # Project may already be deleted


@pytest.fixture
def test_alignerr_project(client, test_project):
    """Create a test AlignerrProject instance using the builder pattern."""
    return (
        AlignerrWorkspace.from_labelbox(client)
        .project_builder()
        .set_name(test_project.name)
        .set_media_type(test_project.media_type)
        .create(skip_validation=True)
    )


def test_alignerr_project_initialization_error(client, test_project):
    """Test that direct AlignerrProject initialization raises an error."""
    with pytest.raises(
        RuntimeError, match="AlignerrProject cannot be initialized directly"
    ):
        AlignerrProject(client, test_project)


def test_alignerr_project_property_setter(client, test_alignerr_project):
    """Test AlignerrProject property setter."""
    # Create a new project to test property setting
    new_project_name = f"New Test Project {uuid.uuid4()}"
    new_project = client.create_project(
        name=new_project_name, media_type=MediaType.Image
    )

    try:
        # Test property setter
        test_alignerr_project.project = new_project
        assert test_alignerr_project.project == new_project
        assert test_alignerr_project.project.name == new_project_name
    finally:
        new_project.delete()


def test_alignerr_project_domains(client, test_alignerr_project):
    """Test AlignerrProject domains() method."""
    # Test that domains() returns a PaginatedCollection
    domains = test_alignerr_project.domains()
    assert domains is not None
    # The collection might be empty for a new project, which is expected


def test_alignerr_project_rate_methods_removed(client, test_alignerr_project):
    """Pay By Role rate helpers raise and direct callers to the Rates UI."""
    with pytest.raises(
        NotImplementedError, match=re.escape(PAY_BY_ROLE_REMOVED_MSG)
    ):
        test_alignerr_project.get_project_rates()

    with pytest.raises(
        NotImplementedError, match=re.escape(PAY_BY_ROLE_REMOVED_MSG)
    ):
        test_alignerr_project.set_project_rate(None)
