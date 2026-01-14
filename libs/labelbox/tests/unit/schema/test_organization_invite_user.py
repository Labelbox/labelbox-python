import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock

from labelbox.schema.role import UserGroupRole
from labelbox.schema.organization import Organization


def test_invite_user_duplicate_user_group_roles_same_role_is_deduped():
    client = MagicMock()
    client.get_user.return_value = SimpleNamespace(uid="inviter-id")
    client.execute.return_value = {
        "createInvites": [
            {
                "invite": {
                    "id": "invite-id",
                    "createdAt": "2020-01-01T00:00:00.000Z",
                    "organizationRoleName": "NONE",
                    "inviteeEmail": "someone@example.com",
                    "inviter": {"id": "inviter-id"},
                }
            }
        ]
    }

    organization = Organization(
        client,
        {
            "id": "org-id",
            "name": "Test Org",
            "createdAt": "2020-01-01T00:00:00.000Z",
            "updatedAt": "2020-01-01T00:00:00.000Z",
        },
    )

    org_role_none = SimpleNamespace(uid="org-role-none-id", name="NONE")
    reviewer_role = SimpleNamespace(uid="reviewer-role-id", name="REVIEWER")
    user_group = SimpleNamespace(id="user-group-id")

    user_group_roles = [
        UserGroupRole(user_group=user_group, role=reviewer_role),
        UserGroupRole(user_group=user_group, role=reviewer_role),
    ]

    organization.invite_user(
        email="someone@example.com",
        role=org_role_none,
        user_group_roles=user_group_roles,
    )

    # ensure we only send one entry per group
    args, kwargs = client.execute.call_args
    assert kwargs == {}
    payload = args[1]["data"][0]
    assert payload["userGroupIds"] == ["user-group-id"]
    assert payload["userGroupWithRoleIds"] == [
        {"groupId": "user-group-id", "roleId": "reviewer-role-id"}
    ]


def test_invite_user_duplicate_user_group_roles_conflicting_roles_raises_value_error():
    client = MagicMock()
    client.get_user.return_value = SimpleNamespace(uid="inviter-id")

    organization = Organization(
        client,
        {
            "id": "org-id",
            "name": "Test Org",
            "createdAt": "2020-01-01T00:00:00.000Z",
            "updatedAt": "2020-01-01T00:00:00.000Z",
        },
    )

    org_role_none = SimpleNamespace(uid="org-role-none-id", name="NONE")
    reviewer_role = SimpleNamespace(uid="reviewer-role-id", name="REVIEWER")
    team_manager_role = SimpleNamespace(
        uid="team-manager-role-id", name="TEAM_MANAGER"
    )
    user_group = SimpleNamespace(id="user-group-id")

    user_group_roles = [
        UserGroupRole(user_group=user_group, role=reviewer_role),
        UserGroupRole(user_group=user_group, role=team_manager_role),
    ]

    with pytest.raises(ValueError, match="conflicting role assignments"):
        organization.invite_user(
            email="someone@example.com",
            role=org_role_none,
            user_group_roles=user_group_roles,
        )

    client.execute.assert_not_called()


def test_invite_user_user_group_roles_payload_contains_all_groups():
    client = MagicMock()
    client.get_user.return_value = SimpleNamespace(uid="inviter-id")
    client.execute.return_value = {
        "createInvites": [
            {
                "invite": {
                    "id": "invite-id",
                    "createdAt": "2020-01-01T00:00:00.000Z",
                    "organizationRoleName": "NONE",
                    "inviteeEmail": "someone@example.com",
                    "inviter": {"id": "inviter-id"},
                }
            }
        ]
    }

    organization = Organization(
        client,
        {
            "id": "org-id",
            "name": "Test Org",
            "createdAt": "2020-01-01T00:00:00.000Z",
            "updatedAt": "2020-01-01T00:00:00.000Z",
        },
    )

    org_role_none = SimpleNamespace(uid="org-role-none-id", name="NONE")
    reviewer_role = SimpleNamespace(uid="reviewer-role-id", name="REVIEWER")
    team_manager_role = SimpleNamespace(
        uid="team-manager-role-id", name="TEAM_MANAGER"
    )

    ug1 = SimpleNamespace(id="user-group-1")
    ug2 = SimpleNamespace(id="user-group-2")

    user_group_roles = [
        UserGroupRole(user_group=ug1, role=reviewer_role),
        UserGroupRole(user_group=ug2, role=team_manager_role),
    ]

    organization.invite_user(
        email="someone@example.com",
        role=org_role_none,
        user_group_roles=user_group_roles,
    )

    args, kwargs = client.execute.call_args
    assert kwargs == {}
    payload = args[1]["data"][0]
    assert payload["userGroupIds"] == ["user-group-1", "user-group-2"]
    assert payload["userGroupWithRoleIds"] == [
        {"groupId": "user-group-1", "roleId": "reviewer-role-id"},
        {"groupId": "user-group-2", "roleId": "team-manager-role-id"},
    ]
