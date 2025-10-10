"""Integration tests for ProjectRateV2 functionality."""

import datetime
import uuid

import pytest
from alignerr.schema.project_rate import (
    BillingMode,
    ProjectRateInput,
    ProjectRateV2,
)
from labelbox.schema.media_type import MediaType


@pytest.fixture
def test_project(client):
    """Create a test project for ProjectRateV2 testing."""
    project_name = f"Test ProjectRateV2 {uuid.uuid4()}"
    project = client.create_project(
        name=project_name, media_type=MediaType.Image
    )

    yield project

    # Cleanup
    try:
        project.delete()
    except Exception:
        pass  # Project may already be deleted


def test_project_rate_input_validation():
    """Test ProjectRateInput validation logic."""
    # Test negative rate validation
    with pytest.raises(
        ValueError, match="Rate must be greater than or equal to 0"
    ):
        ProjectRateInput(
            rateForId="",
            isBillRate=True,
            billingMode=BillingMode.BY_HOUR,
            rate=-10.0,
            effectiveSince=datetime.datetime.now().isoformat(),
        )

    # Test isBillRate=True with non-empty rateForId
    with pytest.raises(
        ValueError,
        match="isBillRate indicates that this is a customer bill rate. rateForId must be empty if isBillRate is true",
    ):
        ProjectRateInput(
            rateForId="some-id",
            isBillRate=True,
            billingMode=BillingMode.BY_HOUR,
            rate=25.0,
            effectiveSince=datetime.datetime.now().isoformat(),
        )


def test_get_by_project_id_no_rates(client, test_project):
    """Test get_by_project_id when no rates are set."""
    rates = ProjectRateV2.get_by_project_id(client, test_project.uid)
    assert rates == []


def test_set_and_get_project_rate_customer(client, test_project):
    """Test setting and getting a customer project rate."""
    # Create customer rate input
    rate_input = ProjectRateInput(
        rateForId="",  # Empty string for customer rate
        isBillRate=True,
        billingMode=BillingMode.BY_HOUR,
        rate=25.0,
        effectiveSince=datetime.datetime.now().isoformat(),
    )

    # Set the project rate
    result = ProjectRateV2.set_project_rate(
        client, test_project.uid, rate_input
    )
    assert result is True

    # Get the project rates back
    rates = ProjectRateV2.get_by_project_id(client, test_project.uid)
    assert isinstance(rates, list)
    assert len(rates) >= 1

    # Find the customer rate
    customer_rate = None
    for rate in rates:
        if rate.isBillRate:
            customer_rate = rate
            break

    assert customer_rate is not None
    assert customer_rate.isBillRate is True
    assert customer_rate.billingMode == BillingMode.BY_HOUR
    assert customer_rate.rate == 25.0


def test_multiple_project_rates(client, test_project):
    """Test setting multiple project rates for the same project."""
    # Set customer rate
    customer_rate_input = ProjectRateInput(
        rateForId="",
        isBillRate=True,
        billingMode=BillingMode.BY_HOUR,
        rate=30.0,
        effectiveSince=datetime.datetime.now().isoformat(),
    )

    result1 = ProjectRateV2.set_project_rate(
        client, test_project.uid, customer_rate_input
    )
    assert result1 is True

    # Get available roles for role rate
    roles = client.get_roles()
    role_id = None
    for role in roles.values():
        if role.name == "REVIEWER":
            role_id = role.uid
            break

    if role_id:
        # Set role rate
        role_rate_input = ProjectRateInput(
            rateForId=role_id,
            isBillRate=False,
            billingMode=BillingMode.BY_TASK,
            rate=1.25,
            effectiveSince=datetime.datetime.now().isoformat(),
        )

        result2 = ProjectRateV2.set_project_rate(
            client, test_project.uid, role_rate_input
        )
        assert result2 is True

        # Get all project rates
        rates = ProjectRateV2.get_by_project_id(client, test_project.uid)
        assert isinstance(rates, list)
        assert len(rates) >= 2

        # Verify we have both customer and role rates
        customer_rates = [r for r in rates if r.isBillRate]
        role_rates = [r for r in rates if not r.isBillRate]

        assert len(customer_rates) >= 1
        assert len(role_rates) >= 1
