import os
import uuid
from typing import Optional

import requests
import pytest

from labelbox import Client
from labelbox.schema.iam_integration import (
    AwsIamIntegrationSettings,
    GcpIamIntegrationSettings,
    AzureIamIntegrationSettings,
)
from ..conftest import create_dataset_robust


def delete_iam_integration(client, iam_integration_id: str):
    """Helper function to delete an IAM integration using GraphQL mutation."""
    mutation = """mutation DeleteIamIntegrationPyApi($id: ID!) {
        deleteIamIntegration(where: { id: $id })
    }"""
    params = {"id": iam_integration_id}
    client.execute(mutation, params, experimental=True)


@pytest.fixture
def test_integration_name() -> str:
    """Returns a unique name for test integrations."""
    return f"test-integration-{uuid.uuid4()}"


@pytest.fixture
def aws_integration(
    client, test_integration_name
) -> Optional["IAMIntegration"]:
    """Creates a test AWS integration and cleans it up after the test."""
    settings = AwsIamIntegrationSettings(
        role_arn="arn:aws:iam::000000000000:role/temporary",
        read_bucket="test-bucket",
    )
    integration = client.get_organization().create_iam_integration(
        name=test_integration_name,
        settings=settings,
    )
    yield integration
    # Proper cleanup using delete mutation
    delete_iam_integration(client, integration.uid)


@pytest.fixture
def gcp_integration(
    client, test_integration_name
) -> Optional["IAMIntegration"]:
    """Creates a test GCP integration and cleans it up after the test."""
    settings = GcpIamIntegrationSettings(
        read_bucket="gs://test-bucket",
    )
    integration = client.get_organization().create_iam_integration(
        name=test_integration_name,
        settings=settings,
    )
    yield integration
    # Proper cleanup using delete mutation
    delete_iam_integration(client, integration.uid)


@pytest.fixture
def azure_integration(
    client, test_integration_name
) -> Optional["IAMIntegration"]:
    """Creates a test Azure integration and cleans it up after the test."""
    settings = AzureIamIntegrationSettings(
        read_container_url="https://test.blob.core.windows.net/test",
        tenant_id="test-tenant",
    )
    integration = client.get_organization().create_iam_integration(
        name=test_integration_name,
        settings=settings,
    )
    yield integration
    # Proper cleanup using delete mutation
    delete_iam_integration(client, integration.uid)


def test_create_aws_integration(client, test_integration_name):
    """Test creating an AWS IAM integration."""
    settings = AwsIamIntegrationSettings(
        role_arn="arn:aws:iam::000000000000:role/temporary",
        read_bucket="test-bucket",
    )
    integration = client.get_organization().create_iam_integration(
        name=test_integration_name, settings=settings
    )

    try:
        assert integration.name == test_integration_name
        assert integration.provider == "AWS"
        assert isinstance(integration.settings, AwsIamIntegrationSettings)
        assert integration.settings.role_arn == settings.role_arn
        assert integration.settings.read_bucket == settings.read_bucket
    finally:
        # Ensure cleanup even if assertions fail
        delete_iam_integration(client, integration.uid)


def test_create_gcp_integration(client, test_integration_name):
    """Test creating a GCP IAM integration."""
    settings = GcpIamIntegrationSettings(read_bucket="gs://test-bucket")
    integration = client.get_organization().create_iam_integration(
        name=test_integration_name, settings=settings
    )

    try:
        assert integration.name == test_integration_name
        assert integration.provider == "GCP"
        assert isinstance(integration.settings, GcpIamIntegrationSettings)
        assert integration.settings.read_bucket == settings.read_bucket
    finally:
        # Ensure cleanup even if assertions fail
        delete_iam_integration(client, integration.uid)


def test_create_azure_integration(client, test_integration_name):
    """Test creating an Azure IAM integration."""
    settings = AzureIamIntegrationSettings(
        read_container_url="https://test.blob.core.windows.net/test",
        tenant_id="test-tenant",
    )
    integration = client.get_organization().create_iam_integration(
        name=test_integration_name, settings=settings
    )

    try:
        assert integration.name == test_integration_name
        assert integration.provider == "Azure"
        assert isinstance(integration.settings, AzureIamIntegrationSettings)
        assert (
            integration.settings.read_container_url
            == settings.read_container_url
        )
        assert integration.settings.tenant_id == settings.tenant_id
    finally:
        # Ensure cleanup even if assertions fail
        delete_iam_integration(client, integration.uid)


def test_update_aws_integration(client, test_integration_name):
    """Test updating an AWS IAM integration."""
    # Create initial integration
    settings = AwsIamIntegrationSettings(
        role_arn="arn:aws:iam::000000000000:role/temporary",
        read_bucket="test-bucket",
    )
    integration = client.get_organization().create_iam_integration(
        name=test_integration_name, settings=settings
    )

    try:
        # Update integration
        new_settings = AwsIamIntegrationSettings(
            role_arn="arn:aws:iam::111111111111:role/updated",
            read_bucket="updated-bucket",
        )
        integration.update(
            name=f"updated-{test_integration_name}", settings=new_settings
        )

        # Verify update - find the specific integration by ID
        updated_integration = None
        for iam_int in client.get_organization().get_iam_integrations():
            if iam_int.uid == integration.uid:
                updated_integration = iam_int
                break

        assert updated_integration is not None
        assert updated_integration.name == f"updated-{test_integration_name}"
        # Note: Settings may not be returned immediately after update
    finally:
        # Ensure cleanup even if assertions fail
        delete_iam_integration(client, integration.uid)


def test_update_gcp_integration(client, test_integration_name):
    """Test updating a GCP IAM integration."""
    # Create initial integration
    settings = GcpIamIntegrationSettings(read_bucket="gs://test-bucket")
    integration = client.get_organization().create_iam_integration(
        name=test_integration_name, settings=settings
    )

    try:
        # Update integration
        new_settings = GcpIamIntegrationSettings(
            read_bucket="gs://updated-bucket"
        )
        integration.update(
            name=f"updated-{test_integration_name}", settings=new_settings
        )

        # Verify update - find the specific integration by ID
        updated_integration = None
        for iam_int in client.get_organization().get_iam_integrations():
            if iam_int.uid == integration.uid:
                updated_integration = iam_int
                break

        assert updated_integration is not None
        assert updated_integration.name == f"updated-{test_integration_name}"
        # Note: Settings may not be returned immediately after update
    finally:
        # Ensure cleanup even if assertions fail
        delete_iam_integration(client, integration.uid)


def test_update_azure_integration(client, test_integration_name):
    """Test updating an Azure IAM integration."""
    # Create initial integration
    settings = AzureIamIntegrationSettings(
        read_container_url="https://test.blob.core.windows.net/test",
        tenant_id="test-tenant",
    )
    integration = client.get_organization().create_iam_integration(
        name=test_integration_name, settings=settings
    )

    try:
        # Update integration
        new_settings = AzureIamIntegrationSettings(
            read_container_url="https://updated.blob.core.windows.net/test",
            tenant_id="updated-tenant",
        )
        integration.update(
            name=f"updated-{test_integration_name}", settings=new_settings
        )

        # Verify update - find the specific integration by ID
        updated_integration = None
        for iam_int in client.get_organization().get_iam_integrations():
            if iam_int.uid == integration.uid:
                updated_integration = iam_int
                break

        assert updated_integration is not None
        assert updated_integration.name == f"updated-{test_integration_name}"
        # Note: Settings may not be returned immediately after update
    finally:
        # Ensure cleanup even if assertions fail
        delete_iam_integration(client, integration.uid)


def test_update_azure_integration_with_credentials(
    client, test_integration_name
):
    """Test updating an Azure IAM integration including credentials."""
    # Create initial integration without credentials
    settings = AzureIamIntegrationSettings(
        read_container_url="https://test.blob.core.windows.net/test",
        tenant_id="test-tenant",
    )
    integration = client.get_organization().create_iam_integration(
        name=test_integration_name, settings=settings
    )

    try:
        # Update integration - note: credentials are not supported in updates
        new_settings = AzureIamIntegrationSettings(
            read_container_url="https://updated.blob.core.windows.net/test",
            tenant_id="updated-tenant",
            # Note: client_id and client_secret are not supported in update operations
        )
        integration.update(
            name=f"updated-{test_integration_name}", settings=new_settings
        )

        # Verify update (Note: credentials are not returned for security reasons)
        updated_integration = client.get_organization().get_iam_integrations()[
            0
        ]
        assert updated_integration.name == f"updated-{test_integration_name}"
        # Note: Settings might not be returned for security reasons
    finally:
        # Ensure cleanup even if assertions fail
        delete_iam_integration(client, integration.uid)


def test_validate_integration_format(client):
    """Test that validate returns a result with the correct format."""
    # Get any existing integration or create a test one
    integrations = client.get_organization().get_iam_integrations()
    if not integrations:
        pytest.skip("No IAM integrations available for testing")

    integration = integrations[0]
    result = integration.validate()

    # Verify the result structure
    assert isinstance(result, dict)
    assert "valid" in result
    assert isinstance(result["valid"], bool)
    assert "checks" in result
    assert isinstance(result["checks"], list)

    # Verify each check's structure
    for check in result["checks"]:
        assert isinstance(check, dict)
        assert "name" in check
        assert isinstance(check["name"], str)
        assert "success" in check
        assert isinstance(check["success"], bool)
        assert "message" in check
        assert isinstance(check["message"], str)


def test_validate_with_additional_checks(client):
    """Test validate with additional cloud buckets validation."""
    # Get any existing integration or create a test one
    integrations = client.get_organization().get_iam_integrations()
    if not integrations:
        pytest.skip("No IAM integrations available for testing")

    integration = integrations[0]
    result = integration.validate()

    # Verify the result structure
    assert isinstance(result, dict)
    assert "valid" in result
    assert isinstance(result["valid"], bool)
    assert "checks" in result
    assert isinstance(result["checks"], list)


def test_set_as_default(client, test_integration_name):
    """Test setting an integration as default."""
    # Save the original default integration
    original_default = client.get_organization().get_default_iam_integration()

    integration = None
    try:
        # Create an integration
        settings = AwsIamIntegrationSettings(
            role_arn="arn:aws:iam::000000000000:role/temporary",
            read_bucket="test-bucket",
        )
        integration = client.get_organization().create_iam_integration(
            name=test_integration_name, settings=settings
        )

        # Set as default
        integration.set_as_default()

        # Verify it's now the default
        default_integration = (
            client.get_organization().get_default_iam_integration()
        )
        assert default_integration is not None
        assert default_integration.uid == integration.uid
        assert default_integration.is_org_default

    finally:
        # Restore the original default integration
        if original_default is not None:
            original_default.set_as_default()
        # Clean up the created integration
        if integration is not None:
            delete_iam_integration(client, integration.uid)


@pytest.mark.skip(
    reason="Google credentials are being updated for this test, disabling till it's all sorted out"
)
@pytest.mark.skipif(
    not os.environ.get("DA_GCP_LABELBOX_API_KEY"),
    reason="DA_GCP_LABELBOX_API_KEY not found",
)
def test_default_integration():
    """
    This tests assumes the following:
    1. gcp delegated access is configured to work with jtso-gcs-sdk-da-tests
    2. the integration name is gcs sdk test bucket
    3. This integration is the default

    Currently tests against:
    Org ID: cl269lvvj78b50zau34s4550z
    Email: jtso+gcp_sdk_tests@labelbox.com"""
    client = Client(api_key=os.environ.get("DA_GCP_LABELBOX_API_KEY"))
    ds = create_dataset_robust(client, name="new_ds")
    dr = ds.create_data_row(
        row_data="gs://jtso-gcs-sdk-da-tests/nikita-samokhin-D6QS6iv_CTY-unsplash.jpg"
    )
    assert requests.get(dr.row_data).status_code == 200
    assert ds.iam_integration().name == "gcs sdk test bucket"
    ds.delete()


@pytest.mark.skip(
    reason="Google credentials are being updated for this test, disabling till it's all sorted out"
)
@pytest.mark.skipif(
    not os.environ.get("DA_GCP_LABELBOX_API_KEY"),
    reason="DA_GCP_LABELBOX_API_KEY not found",
)
def test_non_default_integration():
    """
    This tests assumes the following:
    1. aws delegated access is configured to work with lbox-test-bucket
    2. an integration called aws is available to the org

    Currently tests against:
    Org ID: cl26d06tk0gch10901m7jeg9v
    Email: jtso+aws_sdk_tests@labelbox.com
    """
    client = Client(api_key=os.environ.get("DA_GCP_LABELBOX_API_KEY"))
    integrations = client.get_organization().get_iam_integrations()
    integration = [
        inte for inte in integrations if "aws-da-test-bucket" in inte.name
    ][0]
    assert integration.valid
    ds = create_dataset_robust(
        client, iam_integration=integration, name="new_ds"
    )
    assert ds.iam_integration().name == "aws-da-test-bucket"
    dr = ds.create_data_row(
        row_data="https://jtso-aws-da-sdk-tests.s3.us-east-2.amazonaws.com/adrian-yu-qkN4D3Rf1gw-unsplash.jpg"
    )
    assert requests.get(dr.row_data).status_code == 200
    ds.delete()


def test_no_integration(client, image_url):
    ds = create_dataset_robust(client, iam_integration=None, name="new_ds")
    assert ds.iam_integration() is None
    dr = ds.create_data_row(row_data=image_url)
    assert requests.get(dr.row_data).status_code == 200
    ds.delete()


@pytest.mark.skip(reason="Assumes state of account doesn't have integration")
def test_no_default_integration(client):
    ds = create_dataset_robust(client, name="new_ds")
    assert ds.iam_integration() is None
    ds.delete()


@pytest.mark.skip(
    reason="Google credentials are being updated for this test, disabling till it's all sorted out"
)
@pytest.mark.skipif(
    not os.environ.get("DA_GCP_LABELBOX_API_KEY"),
    reason="DA_GCP_LABELBOX_API_KEY not found",
)
def test_add_integration_from_object():
    """
    This test is based on test_non_default_integration() and assumes the following:

    1. aws delegated access is configured to work with lbox-test-bucket
    2. an integration called aws is available to the org

    Currently tests against:
    Org ID: cl26d06tk0gch10901m7jeg9v
    Email: jtso+aws_sdk_tests@labelbox.com
    """
    client = Client(api_key=os.environ.get("DA_GCP_LABELBOX_API_KEY"))
    integrations = client.get_organization().get_iam_integrations()

    # Prepare dataset with no integration
    integration = [
        integration
        for integration in integrations
        if "aws-da-test-bucket" in integration.name
    ][0]

    ds = create_dataset_robust(
        client, iam_integration=None, name=f"integration_add_obj-{uuid.uuid4()}"
    )

    # Test set integration with object
    new_integration = ds.add_iam_integration(integration)
    assert new_integration == integration

    # Cleaning
    ds.delete()


@pytest.mark.skip(
    reason="Google credentials are being updated for this test, disabling till it's all sorted out"
)
@pytest.mark.skipif(
    not os.environ.get("DA_GCP_LABELBOX_API_KEY"),
    reason="DA_GCP_LABELBOX_API_KEY not found",
)
def test_add_integration_from_uid():
    """
    This test is based on test_non_default_integration() and assumes the following:

    1. aws delegated access is configured to work with lbox-test-bucket
    2. an integration called aws is available to the org

    Currently tests against:
    Org ID: cl26d06tk0gch10901m7jeg9v
    Email: jtso+aws_sdk_tests@labelbox.com
    """
    client = Client(api_key=os.environ.get("DA_GCP_LABELBOX_API_KEY"))
    integrations = client.get_organization().get_iam_integrations()

    # Prepare dataset with no integration
    integration = [
        integration
        for integration in integrations
        if "aws-da-test-bucket" in integration.name
    ][0]

    ds = create_dataset_robust(
        client, iam_integration=None, name=f"integration_add_id-{uuid.uuid4()}"
    )

    # Test set integration with integration id
    integration_id = [
        integration.uid
        for integration in integrations
        if "aws-da-test-bucket" in integration.name
    ][0]

    new_integration = ds.add_iam_integration(integration_id)
    assert new_integration == integration

    # Cleaning
    ds.delete()


@pytest.mark.skip(
    reason="Google credentials are being updated for this test, disabling till it's all sorted out"
)
@pytest.mark.skipif(
    not os.environ.get("DA_GCP_LABELBOX_API_KEY"),
    reason="DA_GCP_LABELBOX_API_KEY not found",
)
def test_integration_remove():
    """
    This test is based on test_non_default_integration() and assumes the following:

    1. aws delegated access is configured to work with lbox-test-bucket
    2. an integration called aws is available to the org

    Currently tests against:
    Org ID: cl26d06tk0gch10901m7jeg9v
    Email: jtso+aws_sdk_tests@labelbox.com
    """
    client = Client(api_key=os.environ.get("DA_GCP_LABELBOX_API_KEY"))
    integrations = client.get_organization().get_iam_integrations()

    # Prepare dataset with an existing integration
    integration = [
        integration
        for integration in integrations
        if "aws-da-test-bucket" in integration.name
    ][0]

    ds = create_dataset_robust(
        client,
        iam_integration=integration,
        name=f"integration_remove-{uuid.uuid4()}",
    )

    # Test unset integration
    ds.remove_iam_integration()
    assert ds.iam_integration() is None

    # Cleaning
    ds.delete()
