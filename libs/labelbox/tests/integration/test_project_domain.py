"""Integration tests for ProjectDomain functionality.

These tests interact with the actual Labelbox API to verify ProjectDomain operations.
"""

import pytest
import uuid

from labelbox.alignerr.schema.project_domain import ProjectDomain
from labelbox.schema.media_type import MediaType


@pytest.fixture
def test_project(client):
    """Create a test project for domain testing."""
    project_name = f"Test Project Domain {uuid.uuid4()}"
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
def test_domains(client):
    """Create test domains for testing."""
    domains = []

    # Create multiple test domains
    for i in range(3):
        domain_name = f"Test Domain {i + 1} {uuid.uuid4()}"
        domain = ProjectDomain.create(client, name=domain_name)
        domains.append(domain)

    yield domains

    # Cleanup - deactivate domains
    for domain in domains:
        try:
            domain.deactivate()
        except Exception:
            pass  # Domain may already be deactivated


def test_create_project_domain(client):
    """Test creating a new project domain."""
    domain_name = f"Test Create Domain {uuid.uuid4()}"

    # Create domain
    domain = ProjectDomain.create(client, name=domain_name)

    assert domain is not None
    assert domain.name == domain_name
    assert domain.id is not None
    assert domain.createdAt is not None
    # Cleanup
    try:
        domain.deactivate()
    except Exception:
        pass


def test_activate_project_domain(client, test_domains):
    """Test activating a project domain."""
    domain = test_domains[0]

    # Initially, domain should be active (created domains are active by default)
    assert domain.deactivatedAt is None

    # Deactivate first
    deactivated_domain = domain.deactivate()
    assert deactivated_domain.deactivatedAt is not None

    # Then activate
    activated_domain = deactivated_domain.activate()
    assert activated_domain.deactivatedAt is None
    assert activated_domain.id == domain.id


def test_deactivate_project_domain(client, test_domains):
    """Test deactivating a project domain."""
    domain = test_domains[0]

    # Initially, domain should be active
    assert domain.deactivatedAt is None

    # Deactivate
    deactivated_domain = domain.deactivate()
    assert deactivated_domain.deactivatedAt is not None
    assert deactivated_domain.id == domain.id


def test_connect_project_to_domains(client, test_project, test_domains):
    """Test connecting a project to multiple domains."""
    domain_ids = [domain.id for domain in test_domains]

    # Connect project to domains
    result = ProjectDomain.connect_project_to_domains(
        client, project_id=test_project.uid, domain_ids=domain_ids
    )

    assert result is True


def test_search_project_domains(client, test_domains):
    """Test searching project domains with various filters."""
    # Test 1: Search without filters - should return all domains
    results = ProjectDomain.search(client)
    assert results is not None
    domain_list = list(results)
    assert isinstance(domain_list, list)
    # Should find at least our test domains
    assert len(domain_list) >= len(test_domains)

    # Test 2: Search by specific name - should find exact match
    target_domain = test_domains[0]
    search_results = ProjectDomain.search(
        client, search_by_name=target_domain.name
    )
    found_domains = list(search_results)
    assert len(found_domains) >= 1
    assert any(domain.name == target_domain.name for domain in found_domains)

    # Test 3: Search by partial name - should find matches
    partial_name = "Test Domain"
    partial_results = ProjectDomain.search(client, search_by_name=partial_name)
    partial_domains = list(partial_results)
    assert len(partial_domains) >= len(test_domains)
    assert all("Test Domain" in domain.name for domain in partial_domains)

    # Test 4: Search for non-existent domain - should return empty
    non_existent_results = ProjectDomain.search(
        client, search_by_name="NonExistentDomain12345"
    )
    non_existent_domains = list(non_existent_results)
    assert len(non_existent_domains) == 0

    # Test 5: Search with pagination parameters
    # Note: PaginatedCollection automatically fetches all pages, so limit only affects individual page size
    paginated_results = ProjectDomain.search(client, limit=2, offset=0)
    paginated_domains = list(paginated_results)
    # Should still find all domains since PaginatedCollection fetches all pages
    assert len(paginated_domains) >= len(test_domains)

    # Test 6: Search with include_archived parameter
    archived_results = ProjectDomain.search(client, include_archived=True)
    archived_domains = list(archived_results)
    assert isinstance(archived_domains, list)

    # Test 7: Verify domain properties in search results
    if found_domains:
        domain = found_domains[0]
        assert hasattr(domain, "id")
        assert hasattr(domain, "name")
        assert hasattr(domain, "createdAt")
        assert hasattr(domain, "updatedAt")
        assert hasattr(domain, "deactivatedAt")
        assert hasattr(domain, "ratingsCount")
        assert domain.id is not None
        assert domain.name is not None
