"""Integration tests for AlignerrProjectFactory functionality."""

import tempfile
import os
import re
import yaml
from pathlib import Path

import pytest

from labelbox import Client
from alignerr.alignerr_project import PAY_BY_ROLE_REMOVED_MSG
from alignerr.alignerr_project_factory import AlignerrProjectFactory
from alignerr.alignerr_project_builder import ValidationType
from labelbox.schema.media_type import MediaType


def test_create_alignerr_project_from_yaml_basic(client: Client):
    """Test creating an AlignerrProject from a basic YAML configuration."""
    config = {"name": "TestFactoryProject", "media_type": "IMAGE"}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config, f)
        yaml_file_path = f.name

    try:
        factory = AlignerrProjectFactory(client)
        alignerr_project = factory.create(yaml_file_path, skip_validation=True)

        assert alignerr_project is not None
        assert alignerr_project.project.name == "TestFactoryProject"
        assert alignerr_project.project.media_type == MediaType.Image

        alignerr_project.project.delete()
    finally:
        os.unlink(yaml_file_path)


def test_create_alignerr_project_from_yaml_with_rates_raises(client: Client):
    """Legacy rates YAML keys raise and direct callers to the Rates UI."""
    config = {
        "name": "TestFactoryProjectWithRates",
        "media_type": "IMAGE",
        "rates": {
            "labeler": {
                "rate": 0.50,
                "billing_mode": "BY_TASK",
                "effective_since": "2024-01-01T00:00:00",
            },
        },
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config, f)
        yaml_file_path = f.name

    try:
        factory = AlignerrProjectFactory(client)
        with pytest.raises(ValueError, match=re.escape(PAY_BY_ROLE_REMOVED_MSG)):
            factory.create(yaml_file_path, skip_validation=True)
    finally:
        os.unlink(yaml_file_path)


def test_create_alignerr_project_from_yaml_with_customer_rate_raises(
    client: Client,
):
    """Legacy customer_rate YAML key raises and directs callers to the Rates UI."""
    config = {
        "name": "TestFactoryProjectWithCustomerRate",
        "media_type": "IMAGE",
        "customer_rate": {
            "rate": 25.0,
            "billing_mode": "BY_HOUR",
            "effective_since": "2024-01-01T00:00:00",
        },
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config, f)
        yaml_file_path = f.name

    try:
        factory = AlignerrProjectFactory(client)
        with pytest.raises(ValueError, match=re.escape(PAY_BY_ROLE_REMOVED_MSG)):
            factory.create(yaml_file_path, skip_validation=True)
    finally:
        os.unlink(yaml_file_path)


def test_create_alignerr_project_from_yaml_validation_error(client: Client):
    """Test that validation errors are raised for incomplete configurations."""
    config = {
        "name": "TestProject"
        # Missing media_type
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config, f)
        yaml_file_path = f.name

    try:
        factory = AlignerrProjectFactory(client)

        with pytest.raises(ValueError, match="Required field 'media_type' is missing"):
            factory.create(yaml_file_path)
    finally:
        os.unlink(yaml_file_path)


def test_create_alignerr_project_from_yaml_invalid_media_type(client: Client):
    """Test that invalid media types raise appropriate errors."""
    config = {"name": "TestProject", "media_type": "INVALID_MEDIA_TYPE"}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config, f)
        yaml_file_path = f.name

    try:
        factory = AlignerrProjectFactory(client)

        with pytest.raises(ValueError, match="Invalid media_type"):
            factory.create(yaml_file_path, skip_validation=True)
    finally:
        os.unlink(yaml_file_path)


def test_create_alignerr_project_from_yaml_file_not_found(client: Client):
    """Test that missing YAML files raise appropriate errors."""
    factory = AlignerrProjectFactory(client)

    with pytest.raises(FileNotFoundError, match="YAML file not found"):
        factory.create("nonexistent_file.yaml")


def test_create_alignerr_project_from_yaml_with_domains(client: Client):
    """Test creating an AlignerrProject from YAML with domains configuration."""
    from alignerr.schema.project_domain import ProjectDomain
    import uuid
    import time

    # Create test domains first
    domain1_name = f"TestDomain1_{uuid.uuid4()}"
    domain2_name = f"TestDomain2_{uuid.uuid4()}"

    domain1 = ProjectDomain.create(client, name=domain1_name)
    domain2 = ProjectDomain.create(client, name=domain2_name)

    # Add a small delay to allow domains to be searchable
    time.sleep(0.5)

    config = {
        "name": "TestFactoryProjectWithDomains",
        "media_type": "IMAGE",
        "domains": [domain1_name, domain2_name],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config, f)
        yaml_file_path = f.name

    try:
        factory = AlignerrProjectFactory(client)
        alignerr_project = factory.create(
            yaml_file_path, skip_validation=[ValidationType.PROJECT_OWNER]
        )

        assert alignerr_project is not None
        assert alignerr_project.project.name == "TestFactoryProjectWithDomains"

        # Verify domains were added
        domain_count = sum(1 for _ in alignerr_project.domains())
        assert domain_count == 2

        alignerr_project.project.delete()
    finally:
        os.unlink(yaml_file_path)
        # Cleanup domains
        try:
            domain1.deactivate()
            domain2.deactivate()
        except Exception:
            pass


def test_create_alignerr_project_from_yaml_with_tags(client: Client):
    """Test creating an AlignerrProject from YAML with enhanced resource tags configuration."""
    from alignerr.schema.enchanced_resource_tags import (
        EnhancedResourceTag,
        ResourceTagType,
    )
    import uuid

    # Create test resource tags
    tag1_text = f"TestTag1_{uuid.uuid4().hex[:8]}"
    tag2_text = f"TestTag2_{uuid.uuid4().hex[:8]}"

    tag1 = EnhancedResourceTag.create(
        client,
        text=tag1_text,
        color="#FF5733",
        tag_type=ResourceTagType.Default,
    )
    tag2 = EnhancedResourceTag.create(
        client,
        text=tag2_text,
        color="#33FF57",
        tag_type=ResourceTagType.Billing,
    )

    config = {
        "name": "TestFactoryProjectWithTags",
        "media_type": "IMAGE",
        "tags": [
            {"text": tag1_text, "type": "Default"},
            {"text": tag2_text, "type": "Billing"},
        ],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config, f)
        yaml_file_path = f.name

    try:
        factory = AlignerrProjectFactory(client)
        alignerr_project = factory.create(
            yaml_file_path, skip_validation=[ValidationType.PROJECT_OWNER]
        )

        assert alignerr_project is not None
        assert alignerr_project.project.name == "TestFactoryProjectWithTags"

        # Verify resource tags were added
        enhanced_tags = alignerr_project.get_tags()
        assert len(enhanced_tags) >= 1  # At least one tag should be present

        alignerr_project.project.delete()
    finally:
        os.unlink(yaml_file_path)
        # Cleanup resource tags
        try:
            tag1.delete()
            tag2.delete()
        except Exception:
            pass


def test_create_alignerr_project_from_yaml_with_project_owner(client: Client):
    """Test creating an AlignerrProject from YAML with project owner configuration."""
    # Get the current user as the project owner
    current_user = client.get_user()

    config = {
        "name": "TestFactoryProjectWithOwner",
        "media_type": "IMAGE",
        "project_owner": current_user.email,
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config, f)
        yaml_file_path = f.name

    try:
        factory = AlignerrProjectFactory(client)
        alignerr_project = factory.create(yaml_file_path)

        assert alignerr_project is not None
        assert alignerr_project.project.name == "TestFactoryProjectWithOwner"

        # Verify project owner was set
        project_boost_workforce = alignerr_project.get_project_owner()
        if project_boost_workforce:
            assert project_boost_workforce.projectOwnerUserId == current_user.uid
            assert project_boost_workforce.projectOwner.uid == current_user.uid

        alignerr_project.project.delete()
    finally:
        os.unlink(yaml_file_path)


def test_create_alignerr_project_from_yaml_comprehensive(client: Client):
    """Test creating an AlignerrProject from the comprehensive YAML asset file."""
    # Get the current user for project owner
    current_user = client.get_user()

    # Path to the comprehensive test YAML file
    yaml_file_path = (
        Path(__file__).parent.parent / "assets" / "test_project_comprehensive.yaml"
    )

    # Read and modify the YAML to use current user's email and remove domains/tags that require existing resources
    with open(yaml_file_path, "r") as f:
        config = yaml.safe_load(f)

    # Update project owner to current user's email
    config["project_owner"] = current_user.email

    # Remove domains and tags that require existing resources for this test
    if "domains" in config:
        del config["domains"]
    if "tags" in config:
        del config["tags"]

    # Create temporary YAML file with updated config
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config, f)
        temp_yaml_path = f.name

    try:
        factory = AlignerrProjectFactory(client)
        alignerr_project = factory.create(temp_yaml_path)

        assert alignerr_project is not None
        assert alignerr_project.project.name == "TestComprehensiveProject"
        assert alignerr_project.project.media_type == MediaType.Image

        # Verify project owner was set
        project_boost_workforce = alignerr_project.get_project_owner()
        if project_boost_workforce:
            assert project_boost_workforce.projectOwnerUserId == current_user.uid

        alignerr_project.project.delete()
    finally:
        os.unlink(temp_yaml_path)


def test_create_alignerr_project_from_yaml_selective_validation(client: Client):
    """Test creating an AlignerrProject from YAML with selective validation."""
    config = {
        "name": "TestFactoryProjectSelectiveValidation",
        "media_type": "IMAGE",
        # Note: No project owner set, but we skip that validation
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config, f)
        yaml_file_path = f.name

    try:
        factory = AlignerrProjectFactory(client)
        # Skip project owner validation
        alignerr_project = factory.create(
            yaml_file_path, skip_validation=[ValidationType.PROJECT_OWNER]
        )

        assert alignerr_project is not None
        assert alignerr_project.project.name == "TestFactoryProjectSelectiveValidation"

        alignerr_project.project.delete()
    finally:
        os.unlink(yaml_file_path)


def test_create_alignerr_project_from_yaml_invalid_tags(client: Client):
    """Test that invalid tag configurations raise appropriate errors."""
    config = {
        "name": "TestProject",
        "media_type": "IMAGE",
        "tags": [
            {"text": "TestTag1", "type": "InvalidType"},  # Invalid tag type
        ],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config, f)
        yaml_file_path = f.name

    try:
        factory = AlignerrProjectFactory(client)

        with pytest.raises(ValueError, match="Invalid tag type 'InvalidType'"):
            factory.create(yaml_file_path, skip_validation=True)
    finally:
        os.unlink(yaml_file_path)
