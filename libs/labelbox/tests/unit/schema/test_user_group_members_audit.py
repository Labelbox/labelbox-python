from collections import defaultdict
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from lbox.exceptions import UnprocessableEntityError

from labelbox import Client
from labelbox.schema.role import Role
from labelbox.schema.user import User
from labelbox.schema.user_group import UserGroup, UserGroupMember
from labelbox.schema.user_group_audit import (
    UserGroupAuditActorKind,
    UserGroupAuditChannel,
    UserGroupAuditEventType,
)


def make_user(uid):
    values = defaultdict(lambda: None)
    values["id"] = uid
    values["email"] = f"{uid}@example.com"
    return User(MagicMock(Client), values)


def make_role(uid, name="LABELER"):
    return Role(MagicMock(Client), {"id": uid, "name": name})


@pytest.fixture
def client():
    return MagicMock(Client)


@pytest.fixture
def group(client):
    return UserGroup(client, id="group_id", name="Vendors")


def event_node(**overrides):
    node = {
        "id": "event_1",
        "groupId": "group_id",
        "groupName": "Vendors",
        "type": "MEMBER_REMOVED",
        "occurredAt": "2026-10-20T12:00:00.000Z",
        "actorKind": "AUTOMATION",
        "channel": "API",
        "actorUserId": "admin_id",
        "automation": "API key: sync",
        "memberUserId": "user_1",
        "previousRoleId": "labeler_id",
        "previousRoleName": "Labeler",
        "roleId": None,
        "roleName": None,
        "projectId": None,
        "projectName": None,
    }
    node.update(overrides)
    return node


class TestAddMembers:
    def test_sends_user_roles_and_returns_added(self, group, client):
        client.execute.return_value = {
            "addUsersToGroupsV2": {
                "results": [
                    {
                        "success": True,
                        "added": ["user_1"],
                        "error": None,
                        "batchJob": None,
                    }
                ]
            }
        }

        added = group.add_members(
            [UserGroupMember(make_user("user_1"), make_role("labeler_id"))],
            notify_members=True,
        )

        assert added == ["user_1"]
        query, params = client.execute.call_args[0]
        assert "addUsersToGroupsV2" in query
        assert params == {
            "id": "group_id",
            "userRoles": [{"userId": "user_1", "roleId": "labeler_id"}],
            "notifyMembers": True,
        }

    def test_drives_batch_job_until_complete(self, group, client):
        client.execute.side_effect = [
            {
                "addUsersToGroupsV2": {
                    "results": [
                        {
                            "success": True,
                            "added": ["user_1"],
                            "error": None,
                            "batchJob": {
                                "batchJobId": "job_1",
                                "isComplete": False,
                            },
                        }
                    ]
                }
            },
            {
                "continueAddUsersToGroupBatch": {
                    "batchJob": {"batchJobId": "job_1", "isComplete": False}
                }
            },
            {
                "continueAddUsersToGroupBatch": {
                    "batchJob": {"batchJobId": "job_1", "isComplete": True}
                }
            },
        ]

        group.add_members(
            [UserGroupMember(make_user("user_1"), make_role("labeler_id"))]
        )

        assert client.execute.call_count == 3
        assert client.execute.call_args[0][1] == {"batchJobId": "job_1"}

    def test_raises_when_server_rejects(self, group, client):
        client.execute.return_value = {
            "addUsersToGroupsV2": {
                "results": [
                    {
                        "success": False,
                        "added": None,
                        "error": "User not in workspace",
                        "batchJob": None,
                    }
                ]
            }
        }

        with pytest.raises(
            UnprocessableEntityError, match="User not in workspace"
        ):
            group.add_members(
                [UserGroupMember(make_user("user_1"), make_role("labeler_id"))]
            )

    def test_rejects_duplicate_and_empty_members(self, group, client):
        member = UserGroupMember(make_user("user_1"), make_role("labeler_id"))
        with pytest.raises(ValueError, match="only once"):
            group.add_members([member, member])
        with pytest.raises(ValueError, match="At least one"):
            group.add_members([])
        client.execute.assert_not_called()

    def test_requires_group_id(self, client):
        with pytest.raises(ValueError, match="Group id"):
            UserGroup(client).add_members([])


class TestRemoveMembers:
    def test_sends_user_ids_and_options(self, group, client):
        client.execute.return_value = {
            "removeUsersFromGroupV2": {"success": True}
        }

        assert group.remove_members(
            [make_user("user_1"), make_user("user_2"), make_user("user_1")],
            notify_users=False,
            reason="Contract ended",
        )

        query, params = client.execute.call_args[0]
        assert "removeUsersFromGroupV2" in query
        assert params == {
            "id": "group_id",
            "data": {
                "userIds": ["user_1", "user_2"],
                "notifyUsers": False,
                "reason": "Contract ended",
            },
        }
        assert (
            client.execute.call_args.kwargs["raise_return_resource_not_found"]
            is True
        )

    def test_rejects_empty_users(self, group, client):
        with pytest.raises(ValueError, match="At least one"):
            group.remove_members([])
        client.execute.assert_not_called()


class TestListMembers:
    def test_returns_members_with_group_roles(self, group, client):
        client.execute.return_value = {
            "userGroupV2": {
                "members": {
                    "nodes": [
                        {"id": "user_1", "email": "user_1@example.com"},
                        {"id": "user_2", "email": "user_2@example.com"},
                    ],
                    "userGroupRoles": [
                        {"userId": "user_1", "roleId": "labeler_id"},
                        {"userId": "user_2", "roleId": "reviewer_id"},
                    ],
                }
            }
        }
        roles = {
            "LABELER": make_role("labeler_id", "LABELER"),
            "REVIEWER": make_role("reviewer_id", "REVIEWER"),
        }
        group.name = "Unsaved name"

        with patch("labelbox.schema.role.get_roles", return_value=roles):
            members = group.list_members()

        assert {(m.user.uid, m.role.uid) for m in members} == {
            ("user_1", "labeler_id"),
            ("user_2", "reviewer_id"),
        }
        assert group.name == "Unsaved name"


class TestAuditEvents:
    def test_group_audit_events_filters_and_parses(self, group, client):
        client.execute.return_value = {
            "userGroupAuditEvents": {
                "nodes": [event_node()],
                "nextCursor": None,
            }
        }

        events = list(
            group.audit_events(
                member=make_user("user_1"),
                actor_kind="AUTOMATION",
                types=[UserGroupAuditEventType.MEMBER_REMOVED],
                occurred_after=datetime(2026, 10, 1),
            )
        )

        assert len(events) == 1
        event = events[0]
        assert event.type is UserGroupAuditEventType.MEMBER_REMOVED
        assert event.actor_kind is UserGroupAuditActorKind.AUTOMATION
        assert event.channel is UserGroupAuditChannel.API
        assert event.member_user_id == "user_1"
        assert event.occurred_at == datetime(
            2026, 10, 20, 12, tzinfo=timezone.utc
        )

        query, params = client.execute.call_args[0]
        assert "userGroupAuditEvents" in query
        assert params["where"] == {
            "groupId": "group_id",
            "memberUserId": "user_1",
            "actorKind": "AUTOMATION",
            "types": ["MEMBER_REMOVED"],
            "occurredAfter": "2026-10-01T00:00:00.000Z",
        }

    def test_get_audit_events_without_group_and_unknown_values(self, client):
        client.execute.return_value = {
            "userGroupAuditEvents": {
                "nodes": [
                    event_node(
                        type="SOMETHING_NEW",
                        channel="NEW_CHANNEL",
                        groupName=None,
                    )
                ],
                "nextCursor": None,
            }
        }

        events = list(UserGroup.get_audit_events(client, project="project_1"))

        assert events[0].type == "SOMETHING_NEW"
        assert events[0].channel == "NEW_CHANNEL"
        assert events[0].group_name is None
        assert client.execute.call_args[0][1]["where"] == {
            "projectId": "project_1"
        }

    def test_rejects_bad_filters(self, group, client):
        with pytest.raises(ValueError):
            group.audit_events(actor_kind="ROBOT")
        with pytest.raises(ValueError, match="before"):
            group.audit_events(
                occurred_after="2026-10-02", occurred_before="2026-10-01"
            )
        client.execute.assert_not_called()
