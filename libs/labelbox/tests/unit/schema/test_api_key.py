from datetime import datetime, timezone
from ipaddress import ip_address, ip_network
from unittest.mock import MagicMock, patch

import pytest

from labelbox.schema.api_key import ApiKey
from labelbox.schema.timeunit import TimeUnit


def _api_key_data(**overrides):
    data = {
        "id": "key-1",
        "name": "Restricted key",
        "createdAt": "2026-09-17T12:00:00.000Z",
        "updatedAt": "2026-09-17T12:00:00.000Z",
        "revoked": False,
        "expiresAtEpoch": int(
            datetime(2030, 1, 1, tzinfo=timezone.utc).timestamp()
        ),
        "createdByUserId": "user-1",
        "userId": "user-1",
        "allowedIpCidrs": ["203.0.113.10", "198.51.100.0/24"],
    }
    data.update(overrides)
    return data


def test_create_api_key_validates_and_serializes_ip_allowlist():
    client = MagicMock()
    client.execute.return_value = {
        "createApiKey": {"id": "key-1", "jwt": "secret"}
    }

    with (
        patch.object(ApiKey, "_get_user", return_value="user-1"),
        patch.object(
            ApiKey, "_get_available_api_key_roles", return_value=["Admin"]
        ),
    ):
        result = ApiKey.create_api_key(
            client,
            name="Restricted key",
            user="person@example.com",
            role="Admin",
            validity=5,
            time_unit=TimeUnit.MINUTE,
            allowed_ip_cidrs=[
                "203.0.113.10",
                ip_network("198.51.100.0/24"),
                ip_address("2001:0db8::1"),
                "203.0.113.10",
            ],
        )

    assert result == {"id": "key-1", "jwt": "secret"}
    query, variables = client.execute.call_args.args
    assert "$allowedIpCidrs: [String!]" in query
    assert variables["allowedIpCidrs"] == [
        "203.0.113.10",
        "198.51.100.0/24",
        "2001:db8::1",
    ]


@pytest.mark.parametrize(
    "allowed_ip_cidrs",
    [
        "203.0.113.10",
        ["not-an-ip"],
        ["192.0.2.10/24"],
        [""],
        [1234],
        [f"192.0.2.{index}" for index in range(51)],
    ],
)
def test_create_api_key_rejects_invalid_ip_allowlist_before_api_calls(
    allowed_ip_cidrs,
):
    client = MagicMock()

    with pytest.raises(ValueError, match="allowed_ip_cidrs|Invalid IP"):
        ApiKey.create_api_key(
            client,
            name="Restricted key",
            user="person@example.com",
            role="Admin",
            validity=5,
            time_unit=TimeUnit.MINUTE,
            allowed_ip_cidrs=allowed_ip_cidrs,
        )

    client.execute.assert_not_called()
    client.get_organization.assert_not_called()


def test_get_api_keys_exposes_allowed_ip_cidrs():
    client = MagicMock()
    client.execute.return_value = {
        "user": {
            "apiKeys": [_api_key_data()],
            "apiKeysOtherUsers": [],
        }
    }

    api_keys = ApiKey.get_api_keys(client)

    assert len(api_keys) == 1
    assert api_keys[0].allowed_ip_cidrs == [
        "203.0.113.10",
        "198.51.100.0/24",
    ]
    assert "allowedIpCidrs" in client.execute.call_args.args[0]


def test_get_api_keys_normalizes_null_allowlist_to_empty_list():
    client = MagicMock()
    client.execute.return_value = {
        "user": {
            "apiKeys": [_api_key_data(allowedIpCidrs=None)],
            "apiKeysOtherUsers": [],
        }
    }

    api_keys = ApiKey.get_api_keys(client)

    assert api_keys[0].allowed_ip_cidrs == []


def test_create_api_key_without_allowlist_sends_null():
    client = MagicMock()
    client.execute.return_value = {
        "createApiKey": {"id": "key-1", "jwt": "secret"}
    }

    with (
        patch.object(ApiKey, "_get_user", return_value="user-1"),
        patch.object(
            ApiKey, "_get_available_api_key_roles", return_value=["Admin"]
        ),
    ):
        ApiKey.create_api_key(
            client,
            name="Unrestricted key",
            user="person@example.com",
            role="Admin",
            validity=5,
            time_unit=TimeUnit.MINUTE,
        )

    assert client.execute.call_args.args[1]["allowedIpCidrs"] is None
