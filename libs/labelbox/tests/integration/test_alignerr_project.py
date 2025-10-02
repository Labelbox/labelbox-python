"""Integration tests for AlignerrProject functionality.

These tests interact with the actual Labelbox API to verify AlignerrProject operations.
"""

import datetime
import uuid

import pytest
from labelbox.alignerr.alignerr_project import AlignerrProject
from labelbox.alignerr.schema.project_rate import BillingMode, ProjectRateInput
from labelbox.schema.media_type import MediaType


@pytest.fixture
def test_project(client):
    """Create a test project for AlignerrProject testing."""
    project_name = f"Test AlignerrProject {uuid.uuid4()}"
    project = client.create_project(
        name=project_name, media_type=MediaType.Image
    )

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
        client.alignerr_workspace.project_builder()
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


def test_alignerr_project_get_project_rates_no_rates(
    client, test_alignerr_project
):
    """Test get_project_rates() when no rates are set."""
    # For a new project without rates, this should return an empty list
    project_rates = test_alignerr_project.get_project_rates()
    assert project_rates == []


def test_alignerr_project_set_and_get_project_rates(
    client, test_alignerr_project
):
    """Test setting and getting project rates."""
    # Create a project rate input for a customer rate (isBillRate=True requires empty rateForId)
    project_rate_input = ProjectRateInput(
        rateForId="",  # Empty string for customer rate
        isBillRate=True,
        billingMode=BillingMode.BY_HOUR,
        rate=25.0,
        effectiveSince=datetime.datetime.now().isoformat(),
        effectiveUntil=None,
    )

    # Set the project rate
    result = test_alignerr_project.set_project_rate(project_rate_input)
    assert result is True  # Should return success status

    # Get the project rates back
    project_rates = test_alignerr_project.get_project_rates()
    # Should return a list with at least one rate
    assert isinstance(project_rates, list)
    assert len(project_rates) >= 1
    # Note: The actual rate retrieval might depend on the API implementation
    # This test verifies the method calls work without errors
