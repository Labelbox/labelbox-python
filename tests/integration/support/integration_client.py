import os
import re
import uuid
from enum import Enum
from typing import Tuple

import requests

from labelbox import Client

EPHEMERAL_BASE_URL = "http://lb-api-public"


class Environ(Enum):
    LOCAL = 'local'
    PROD = 'prod'
    STAGING = 'staging'
    ONPREM = 'onprem'
    CUSTOM = 'custom'
    STAGING_EU = 'staging-eu'
    EPHEMERAL = 'ephemeral'  # Used for testing PRs with ephemeral environments


def ephemeral_endpoint() -> str:
    return os.getenv('LABELBOX_TEST_BASE_URL', EPHEMERAL_BASE_URL)


def graphql_url(environ: str) -> str:
    if environ == Environ.PROD:
        return 'https://api.labelbox.com/graphql'
    elif environ == Environ.STAGING:
        return 'https://api.lb-stage.xyz/graphql'
    elif environ == Environ.STAGING_EU:
        return 'https://api.eu-de.lb-stage.xyz/graphql'
    elif environ == Environ.ONPREM:
        hostname = os.environ.get('LABELBOX_TEST_ONPREM_HOSTNAME', None)
        if hostname is None:
            raise Exception(f"Missing LABELBOX_TEST_ONPREM_INSTANCE")
        return f"{hostname}/api/_gql"
    elif environ == Environ.CUSTOM:
        graphql_api_endpoint = os.environ.get(
            'LABELBOX_TEST_GRAPHQL_API_ENDPOINT')
        if graphql_api_endpoint is None:
            raise Exception(f"Missing LABELBOX_TEST_GRAPHQL_API_ENDPOINT")
        return graphql_api_endpoint
    elif environ == Environ.EPHEMERAL:
        return f"{ephemeral_endpoint()}/graphql"
    return 'http://host.docker.internal:8080/graphql'


def rest_url(environ: str) -> str:
    if environ == Environ.PROD:
        return 'https://api.labelbox.com/api/v1'
    elif environ == Environ.STAGING:
        return 'https://api.lb-stage.xyz/api/v1'
    elif environ == Environ.STAGING_EU:
        return 'https://api.eu-de.lb-stage.xyz/api/v1'
    elif environ == Environ.CUSTOM:
        rest_api_endpoint = os.environ.get('LABELBOX_TEST_REST_API_ENDPOINT')
        if rest_api_endpoint is None:
            raise Exception(f"Missing LABELBOX_TEST_REST_API_ENDPOINT")
        return rest_api_endpoint
    elif environ == Environ.EPHEMERAL:
        return f"{ephemeral_endpoint()}/api/v1"
    return 'http://host.docker.internal:8080/api/v1'


def testing_api_key(environ: str) -> str:
    if environ == Environ.PROD:
        return os.environ["LABELBOX_TEST_API_KEY_PROD"]
    elif environ == Environ.STAGING:
        return os.environ["LABELBOX_TEST_API_KEY_STAGING"]
    elif environ == Environ.STAGING_EU:
        return os.environ["LABELBOX_TEST_API_KEY_STAGING_EU"]
    elif environ == Environ.ONPREM:
        return os.environ["LABELBOX_TEST_API_KEY_ONPREM"]
    elif environ == Environ.CUSTOM:
        return os.environ["LABELBOX_TEST_API_KEY_CUSTOM"]
    return os.environ["LABELBOX_TEST_API_KEY_LOCAL"]


def service_api_key() -> str:
    return os.environ["SERVICE_API_KEY"]


class IntegrationClient(Client):

    def __init__(self, environ: str) -> None:
        api_url = graphql_url(environ)
        api_key = testing_api_key(environ)
        rest_endpoint = rest_url(environ)

        super().__init__(api_key,
                         api_url,
                         enable_experimental=True,
                         rest_endpoint=rest_endpoint)
        self.queries = []

    def execute(self, query=None, params=None, check_naming=True, **kwargs):
        if check_naming and query is not None:
            assert re.match(r"\s*(?:query|mutation) \w+PyApi",
                            query) is not None
        self.queries.append((query, params))
        return super().execute(query, params, **kwargs)


class AdminClient(Client):

    def __init__(self, env):
        """
            The admin client creates organizations and users using admin api described here https://labelbox.atlassian.net/wiki/spaces/AP/pages/2206564433/Internal+Admin+APIs.
        """
        self._api_key = service_api_key()
        self._admin_endpoint = f"{ephemeral_endpoint()}/admin/v1"
        self._api_url = graphql_url(env)
        self._rest_endpoint = rest_url(env)

        super().__init__(self._api_key,
                         self._api_url,
                         enable_experimental=True,
                         rest_endpoint=self._rest_endpoint)

    def _create_organization(self) -> str:
        endpoint = f"{self._admin_endpoint}/organizations/"
        response = requests.post(
            endpoint,
            headers=self.headers,
            json={"name": f"Test Org {uuid.uuid4()}"},
        )

        data = response.json()
        if response.status_code not in [
                requests.codes.created, requests.codes.ok
        ]:
            raise Exception("Failed to create org, message: " +
                            str(data['message']))

        return data['id']

    def _create_user(self, organization_id=None) -> Tuple[str, str]:
        if organization_id is None:
            organization_id = self.organization_id

        endpoint = f"{self._admin_endpoint}/user-identities/"
        identity_id = f"e2e+{uuid.uuid4()}"

        response = requests.post(
            endpoint,
            headers=self.headers,
            json={
                "identityId": identity_id,
                "email": "email@email.com",
                "name": f"tester{uuid.uuid4()}",
                "verificationStatus": "VERIFIED",
            },
        )
        data = response.json()
        if response.status_code not in [
                requests.codes.created, requests.codes.ok
        ]:
            raise Exception("Failed to create user, message: " +
                            str(data['message']))

        user_identity_id = data['identityId']

        endpoint = f"{self._admin_endpoint}/organizations/{organization_id}/users/"
        response = requests.post(
            endpoint,
            headers=self.headers,
            json={
                "identityId": user_identity_id,
                "organizationRole": "Admin"
            },
        )

        data = response.json()
        if response.status_code not in [
                requests.codes.created, requests.codes.ok
        ]:
            raise Exception("Failed to create link user to org, message: " +
                            str(data['message']))

        user_id = data['id']

        endpoint = f"{self._admin_endpoint}/users/{user_id}/token"
        response = requests.get(
            endpoint,
            headers=self.headers,
        )
        data = response.json()
        if response.status_code not in [
                requests.codes.created, requests.codes.ok
        ]:
            raise Exception("Failed to create ephemeral user, message: " +
                            str(data['message']))

        token = data["token"]

        return user_id, token

    def create_api_key_for_user(self) -> str:
        organization_id = self._create_organization()
        _, user_token = self._create_user(organization_id)
        key_name = f"test-key+{uuid.uuid4()}"
        query = """mutation CreateApiKeyPyApi($name: String!) {
                createApiKey(data: {name: $name}) {
                    id
                    jwt
                }
            }
        """
        params = {"name": key_name}
        self.headers["Authorization"] = f"Bearer {user_token}"
        res = self.execute(query, params, error_log_key="errors")

        return res["createApiKey"]["jwt"]


class EphemeralClient(Client):

    def __init__(self, environ=Environ.EPHEMERAL):
        self.admin_client = AdminClient(environ)
        self.api_key = self.admin_client.create_api_key_for_user()
        api_url = graphql_url(environ)
        rest_endpoint = rest_url(environ)

        super().__init__(self.api_key,
                         api_url,
                         enable_experimental=True,
                         rest_endpoint=rest_endpoint)
