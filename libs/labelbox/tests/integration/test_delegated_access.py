import os

import requests
import pytest
import uuid

from labelbox import Client


@pytest.mark.skip(
    reason=
    "Google credentials are being updated for this test, disabling till it's all sorted out"
)
@pytest.mark.skipif(not os.environ.get('DA_GCP_LABELBOX_API_KEY'),
                    reason="DA_GCP_LABELBOX_API_KEY not found")
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
    ds = client.create_dataset(name="new_ds")
    dr = ds.create_data_row(
        row_data=
        "gs://jtso-gcs-sdk-da-tests/nikita-samokhin-D6QS6iv_CTY-unsplash.jpg")
    assert requests.get(dr.row_data).status_code == 200
    assert ds.iam_integration().name == "gcs sdk test bucket"
    ds.delete()


@pytest.mark.skip(
    reason=
    "Google credentials are being updated for this test, disabling till it's all sorted out"
)
@pytest.mark.skipif(not os.environ.get("DA_GCP_LABELBOX_API_KEY"),
                    reason="DA_GCP_LABELBOX_API_KEY not found")
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
        inte for inte in integrations if 'aws-da-test-bucket' in inte.name
    ][0]
    assert integration.valid
    ds = client.create_dataset(iam_integration=integration, name="new_ds")
    assert ds.iam_integration().name == "aws-da-test-bucket"
    dr = ds.create_data_row(
        row_data=
        "https://jtso-aws-da-sdk-tests.s3.us-east-2.amazonaws.com/adrian-yu-qkN4D3Rf1gw-unsplash.jpg"
    )
    assert requests.get(dr.row_data).status_code == 200
    ds.delete()


def test_no_integration(client, image_url):
    ds = client.create_dataset(iam_integration=None, name="new_ds")
    assert ds.iam_integration() is None
    dr = ds.create_data_row(row_data=image_url)
    assert requests.get(dr.row_data).status_code == 200
    ds.delete()


@pytest.mark.skip(reason="Assumes state of account doesn't have integration")
def test_no_default_integration(client):
    ds = client.create_dataset(name="new_ds")
    assert ds.iam_integration() is None
    ds.delete()


@pytest.mark.skip(
    reason=
    "Google credentials are being updated for this test, disabling till it's all sorted out"
)
@pytest.mark.skipif(not os.environ.get("DA_GCP_LABELBOX_API_KEY"),
                    reason="DA_GCP_LABELBOX_API_KEY not found")
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
        integration for integration 
        in integrations 
        if 'aws-da-test-bucket' in integration.name][0]

    ds = client.create_dataset(iam_integration=None, name=f"integration_add_obj-{uuid.uuid4()}")

    # Test set integration with object
    new_integration = ds.add_iam_integration(integration)
    assert new_integration == integration

    # Cleaning
    ds.delete()

@pytest.mark.skip(
    reason=
    "Google credentials are being updated for this test, disabling till it's all sorted out"
)
@pytest.mark.skipif(not os.environ.get("DA_GCP_LABELBOX_API_KEY"),
                    reason="DA_GCP_LABELBOX_API_KEY not found")
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
        integration for integration 
        in integrations 
        if 'aws-da-test-bucket' in integration.name][0]

    ds = client.create_dataset(iam_integration=None, name=f"integration_add_id-{uuid.uuid4()}")

    # Test set integration with integration id
    integration_id = [
        integration.uid for integration 
        in integrations 
        if 'aws-da-test-bucket' in integration.name][0]
    
    new_integration = ds.add_iam_integration(integration_id)
    assert new_integration == integration

    # Cleaning
    ds.delete()

@pytest.mark.skip(
    reason=
    "Google credentials are being updated for this test, disabling till it's all sorted out"
)
@pytest.mark.skipif(not os.environ.get("DA_GCP_LABELBOX_API_KEY"),
                    reason="DA_GCP_LABELBOX_API_KEY not found")
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
        integration for integration 
        in integrations 
        if 'aws-da-test-bucket' in integration.name][0]

    ds = client.create_dataset(iam_integration=integration, name=f"integration_remove-{uuid.uuid4()}")

    # Test unset integration
    ds.remove_iam_integration()
    assert ds.iam_integration() is None

    # Cleaning
    ds.delete()