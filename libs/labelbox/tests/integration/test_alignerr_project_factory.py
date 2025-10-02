"""Integration tests for AlignerrProjectFactory functionality."""

import tempfile
import os
import yaml

import pytest

from labelbox import Client
from labelbox.alignerr.alignerr_project_factory import AlignerrProjectFactory
from labelbox.schema.media_type import MediaType


def test_create_alignerr_project_from_yaml_basic(client: Client):
    """Test creating an AlignerrProject from a basic YAML configuration."""
    config = {"name": "TestFactoryProject", "media_type": "IMAGE"}

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
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


def test_create_alignerr_project_from_yaml_with_rates(client: Client):
    """Test creating an AlignerrProject from YAML with rate configurations."""
    config = {
        "name": "TestFactoryProjectWithRates",
        "media_type": "IMAGE",
        "rates": {
            "labeler": {
                "rate": 0.50,
                "billing_mode": "BY_TASK",
                "effective_since": "2024-01-01T00:00:00",
                "effective_until": "2024-12-31T23:59:59",
            },
            "reviewer": {
                "rate": 0.75,
                "billing_mode": "BY_HOUR",
                "effective_since": "2024-01-01T00:00:00",
            },
        },
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        yaml.dump(config, f)
        yaml_file_path = f.name

    try:
        factory = AlignerrProjectFactory(client)
        alignerr_project = factory.create(yaml_file_path, skip_validation=True)

        assert alignerr_project is not None
        assert alignerr_project.project.name == "TestFactoryProjectWithRates"
        assert alignerr_project.project.media_type == MediaType.Image

        # Verify rates were set by checking project rates
        project_rates = alignerr_project.get_project_rates()
        assert isinstance(project_rates, list)
        assert len(project_rates) >= 1

        alignerr_project.project.delete()
    finally:
        os.unlink(yaml_file_path)


def test_create_alignerr_project_from_yaml_validation_error(client: Client):
    """Test that validation errors are raised for incomplete configurations."""
    config = {
        "name": "TestProject"
        # Missing media_type
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        yaml.dump(config, f)
        yaml_file_path = f.name

    try:
        factory = AlignerrProjectFactory(client)

        with pytest.raises(
            ValueError, match="Required field 'media_type' is missing"
        ):
            factory.create(yaml_file_path)
    finally:
        os.unlink(yaml_file_path)


def test_create_alignerr_project_from_yaml_invalid_media_type(client: Client):
    """Test that invalid media types raise appropriate errors."""
    config = {"name": "TestProject", "media_type": "INVALID_MEDIA_TYPE"}

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
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
