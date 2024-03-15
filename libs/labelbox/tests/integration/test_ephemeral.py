import os
import pytest


@pytest.mark.skipif(not os.environ.get('LABELBOX_TEST_ENVIRON') == 'ephemeral',
                    reason='This test only runs in EPHEMERAL environment')
def test_org_and_user_setup(client, ephmeral_client):
    assert type(client) == ephmeral_client
    assert client.admin_client
    assert client.api_key != client.admin_client.api_key

    organization = client.get_organization()
    assert organization
    user = client.get_user()
    assert user


@pytest.mark.skipif(os.environ.get('LABELBOX_TEST_ENVIRON') == 'ephemeral',
                    reason='This test does not run in EPHEMERAL environment')
def test_integration_client(client, integration_client):
    assert type(client) == integration_client
