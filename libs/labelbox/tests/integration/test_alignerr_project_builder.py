"""Integration tests for ProjectRateV2 functionality."""

import datetime
from labelbox import Client
from labelbox.alignerr.alignerr_project import AlignerrRole
from labelbox.alignerr.schema.project_rate import BillingMode
from labelbox.schema.media_type import MediaType
import pytest


def test_skip_validation(client: Client):
    alignerr_project = (
        client.alignerr_workspace.project_builder()
        .set_name("TestAlignerrProject")
        .set_media_type(MediaType.Image)
        .set_alignerr_role_rate(
            role_name=AlignerrRole.Labeler,
            rate=10.0,
            billing_mode=BillingMode.BY_HOUR,
            effective_since=datetime.datetime.now().isoformat(),
        )
        .create(skip_validation=True)
    )
    assert alignerr_project is not None
    assert alignerr_project.project.name == "TestAlignerrProject"

    alignerr_project.project.delete()


def test_create_alignerr_project_using_builder_validate_input(client: Client):
    with pytest.raises(ValueError):
        client.alignerr_workspace.project_builder().set_name(
            "TestAlignerrProject"
        ).set_media_type(MediaType.Image).set_alignerr_role_rate(
            role_name=AlignerrRole.Labeler,
            rate=10.0,
            billing_mode=BillingMode.BY_HOUR,
            effective_since=datetime.datetime.now().isoformat(),
        ).create()

    alignerr_project = (
        client.alignerr_workspace.project_builder()
        .set_name("TestAlignerrProject2")
        .set_media_type(MediaType.Image)
        .set_alignerr_role_rate(
            role_name=AlignerrRole.Labeler,
            rate=10.0,
            billing_mode=BillingMode.BY_HOUR,
            effective_since=datetime.datetime.now().isoformat(),
        )
        .set_alignerr_role_rate(
            role_name=AlignerrRole.Reviewer,
            rate=10.0,
            billing_mode=BillingMode.BY_HOUR,
            effective_since=datetime.datetime.now().isoformat(),
        )
        .set_customer_rate(
            rate=15.0,
            billing_mode=BillingMode.BY_HOUR,
            effective_since=datetime.datetime.now().isoformat(),
        )
        .create()
    )

    assert alignerr_project is not None
    assert alignerr_project.project.name == "TestAlignerrProject2"

    alignerr_project.project.delete()


def test_create_alignerr_project_using_builder_add_domains(client: Client):
    from labelbox.alignerr.schema.project_domain import ProjectDomain
    import uuid

    # Create test domains first
    domain1_name = f"TestDomain1_{uuid.uuid4()}"
    domain2_name = f"TestDomain2_{uuid.uuid4()}"

    domain1 = ProjectDomain.create(client, name=domain1_name)
    domain2 = ProjectDomain.create(client, name=domain2_name)

    # Add a small delay to allow domains to be searchable
    import time

    time.sleep(0.5)

    try:
        # Add domains using set_domains method
        alignerr_project = (
            client.alignerr_workspace.project_builder()
            .set_name("TestAlignerrProject3")
            .set_media_type(MediaType.Image)
            .set_domains([domain1_name, domain2_name])
            .create(skip_validation=True)
        )
        assert alignerr_project is not None
        assert alignerr_project.project.name == "TestAlignerrProject3"

        # Count domains by iterating through the collection
        domain_count = sum(1 for _ in alignerr_project.domains())
        assert domain_count == 2
        alignerr_project.project.delete()
    finally:
        # Cleanup domains
        try:
            domain1.deactivate()
            domain2.deactivate()
        except Exception:
            pass
