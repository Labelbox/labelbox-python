import requests
import pytest


#@pytest.mark.skip("Can only be tested in specific organizations.")
def test_default_integration(client):
    # This tests assumes the following:
    # 1. gcp delegated access is configured to work with utkarsh-da-test-bucket
    # 2. the integration name is gcp test
    # 3. This integration is the default
    ds = client.create_dataset(name="new_ds")
    dr = ds.create_data_row(
        row_data=
        "gs://utkarsh-da-test-bucket/mathew-schwartz-8rj4sz9YLCI-unsplash.jpg")
    assert requests.get(dr.row_data).status_code == 200
    assert ds.iam_integration().name == "GCP Test"
    ds.delete()


#@pytest.mark.skip("Can only be tested in specific organizations.")
def test_non_default_integration(client):
    # This tests assumes the following:
    # 1. aws delegated access is configured to work with lbox-test-bucket
    # 2. an integration called aws is available to the org
    integrations = client.get_organization().get_iam_integrations()
    integration = [inte for inte in integrations if 'aws' in inte.name][0]
    assert integration.valid
    ds = client.create_dataset(iam_integration=integration, name="new_ds")
    assert ds.iam_integration().name == "aws"
    dr = ds.create_data_row(
        row_data=
        "https://lbox-test-bucket.s3.us-east-1.amazonaws.com/2021_09_08_0hz_Kleki.png"
    )
    assert requests.get(dr.row_data).status_code == 200
    ds.delete()


def test_no_integration(client, image_url):
    ds = client.create_dataset(iam_integration=None, name="new_ds")
    assert ds.iam_integration() is None
    dr = ds.create_data_row(row_data=image_url)
    assert requests.get(dr.row_data).status_code == 200
    ds.delete()
