"""Integration tests for ProjectRateV2 functionality."""

import datetime
from labelbox import Client
from alignerr.alignerr_project import AlignerrRole
from alignerr.schema.project_rate import BillingMode
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

    # Get current user for project owner
    current_user = client.get_user()

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
        .set_project_owner(current_user.email)
        .create()
    )

    assert alignerr_project is not None
    assert alignerr_project.project.name == "TestAlignerrProject2"

    alignerr_project.project.delete()


def test_create_alignerr_project_using_builder_add_domains(client: Client):
    from alignerr.schema.project_domain import ProjectDomain
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


def test_create_alignerr_project_with_rates_domains_and_resource_tags(
    client: Client,
):
    """Test creating an Alignerr project with rates, domains, and enhanced resource tags."""
    from alignerr.schema.project_domain import ProjectDomain
    from alignerr.schema.enchanced_resource_tags import (
        EnhancedResourceTag,
        ResourceTagType,
    )
    import uuid
    import time

    # Create test domains first
    domain1_name = f"TestDomain1_{uuid.uuid4()}"
    domain2_name = f"TestDomain2_{uuid.uuid4()}"

    domain1 = ProjectDomain.create(client, name=domain1_name)
    domain2 = ProjectDomain.create(client, name=domain2_name)

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

    # Add a small delay to allow domains to be searchable
    time.sleep(0.5)

    try:
        # Get current user for project owner
        current_user = client.get_user()

        # Create project with rates, domains, and resource tags
        alignerr_project = (
            client.alignerr_workspace.project_builder()
            .set_name("TestAlignerrProjectWithAll")
            .set_media_type(MediaType.Image)
            .set_alignerr_role_rate(
                role_name=AlignerrRole.Labeler,
                rate=12.0,
                billing_mode=BillingMode.BY_HOUR,
                effective_since=datetime.datetime.now().isoformat(),
            )
            .set_alignerr_role_rate(
                role_name=AlignerrRole.Reviewer,
                rate=15.0,
                billing_mode=BillingMode.BY_HOUR,
                effective_since=datetime.datetime.now().isoformat(),
            )
            .set_customer_rate(
                rate=20.0,
                billing_mode=BillingMode.BY_HOUR,
                effective_since=datetime.datetime.now().isoformat(),
            )
            .set_domains([domain1_name, domain2_name])
            .set_tags([tag1_text, tag2_text], ResourceTagType.Default)
            .set_project_owner(current_user.email)
            .create()
        )

        assert alignerr_project is not None
        assert alignerr_project.project.name == "TestAlignerrProjectWithAll"

        # Verify domains were added
        domain_count = sum(1 for _ in alignerr_project.domains())
        assert domain_count == 2

        # Verify resource tags were added
        enhanced_tags = alignerr_project.get_tags()
        assert len(enhanced_tags) >= 2

        # Check that our specific tags are present
        tag_texts = [tag.text for tag in enhanced_tags]
        assert tag1_text in tag_texts
        assert tag2_text in tag_texts

        alignerr_project.project.delete()
    finally:
        # Cleanup domains
        try:
            domain1.deactivate()
            domain2.deactivate()
        except Exception:
            pass

        # Cleanup resource tags
        try:
            tag1.delete()
            tag2.delete()
        except Exception:
            pass


def test_create_alignerr_project_with_project_owner(client: Client):
    """Test creating an Alignerr project with project owner set."""
    # Get the current user as the project owner
    current_user = client.get_user()

    try:
        # Create project with project owner using email
        alignerr_project = (
            client.alignerr_workspace.project_builder()
            .set_name("TestAlignerrProjectWithOwner")
            .set_media_type(MediaType.Image)
            .set_alignerr_role_rate(
                role_name=AlignerrRole.Labeler,
                rate=10.0,
                billing_mode=BillingMode.BY_HOUR,
                effective_since=datetime.datetime.now().isoformat(),
            )
            .set_alignerr_role_rate(
                role_name=AlignerrRole.Reviewer,
                rate=12.0,
                billing_mode=BillingMode.BY_HOUR,
                effective_since=datetime.datetime.now().isoformat(),
            )
            .set_customer_rate(
                rate=15.0,
                billing_mode=BillingMode.BY_HOUR,
                effective_since=datetime.datetime.now().isoformat(),
            )
            .set_project_owner(current_user.email)
            .create()
        )

        assert alignerr_project is not None
        assert alignerr_project.project.name == "TestAlignerrProjectWithOwner"

        # Verify project owner was set using the AlignerrProject method
        project_boost_workforce = alignerr_project.get_project_owner()

        if project_boost_workforce:
            assert (
                project_boost_workforce.projectOwnerUserId == current_user.uid
            )
            assert project_boost_workforce.projectOwner.uid == current_user.uid

        alignerr_project.project.delete()
    except Exception as e:
        # Clean up if test fails
        try:
            alignerr_project.project.delete()
        except:
            pass
        raise e


def test_create_alignerr_project_selective_validation_skip_multiple(
    client: Client,
):
    """Test creating an Alignerr project with selective validation - skipping multiple validations."""
    from alignerr.alignerr_project_builder import ValidationType

    try:
        # Create project skipping multiple validations
        alignerr_project = (
            client.alignerr_workspace.project_builder()
            .set_name("TestAlignerrProjectSkipMultiple")
            .set_media_type(MediaType.Image)
            .set_alignerr_role_rate(
                role_name=AlignerrRole.Labeler,
                rate=10.0,
                billing_mode=BillingMode.BY_HOUR,
                effective_since=datetime.datetime.now().isoformat(),
            )
            # Note: Missing reviewer rate, customer rate, and project owner, but we skip those validations
            .create(
                skip_validation=[
                    ValidationType.ALIGNERR_RATE,
                    ValidationType.CUSTOMER_RATE,
                    ValidationType.PROJECT_OWNER,
                ]
            )
        )

        assert alignerr_project is not None
        assert (
            alignerr_project.project.name == "TestAlignerrProjectSkipMultiple"
        )

        alignerr_project.project.delete()
    except Exception as e:
        # Clean up if test fails
        try:
            alignerr_project.project.delete()
        except:
            pass
        raise e
