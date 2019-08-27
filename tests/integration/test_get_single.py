import os

import pytest

from labelbox.client import Client


class IntegrationClient(Client):

    def __init__(self):
        super().__init__(os.environ["LABELBOX_TEST_API_KEY"],
                         os.environ["LABELBOX_TEST_ENDPOINT"])

        self.queries = []

    def execute(self, query, params=None):
        self.queries.append((query, params))
        return super().execute(query, params)


@pytest.fixture
def client():
    return IntegrationClient()



def test_get_projects(client):
    projects = list(client.get_projects())
    assert len(projects) > 0
