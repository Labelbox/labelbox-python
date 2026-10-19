from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from labelbox.schema.invite import InviteMemberStatus, InviteResult
from labelbox.schema.organization import Organization


def _organization(client):
    return Organization(
        client,
        {
            "id": "org-id",
            "name": "Test Org",
            "createdAt": "2020-01-01T00:00:00.000Z",
            "updatedAt": "2020-01-01T00:00:00.000Z",
        },
    )


def _echo_results(query, params):
    return {
        "inviteMembers": {
            "results": [
                {
                    "email": email.strip().lower(),
                    "status": "INVITED",
                    "reason": None,
                    "inviteId": f"invite-{index}",
                }
                for index, email in enumerate(params["data"]["emails"])
            ]
        }
    }


def test_invite_users_workspace_wide_payload():
    client = MagicMock()
    client.execute.side_effect = _echo_results
    labeler = SimpleNamespace(uid="labeler-id", name="LABELER")

    results = _organization(client).invite_users(
        ["Ana@X.com", "bob@x.com"], labeler
    )

    query, params = client.execute.call_args.args
    assert "inviteMembers" in query
    assert params == {
        "data": {
            "emails": ["Ana@X.com", "bob@x.com"],
            "workspaceWide": True,
            "roleId": "labeler-id",
            "projectIds": [],
            "groupIds": [],
        }
    }
    assert results == [
        InviteResult("ana@x.com", InviteMemberStatus.INVITED, None, "invite-0"),
        InviteResult("bob@x.com", InviteMemberStatus.INVITED, None, "invite-1"),
    ]


def test_invite_users_project_and_group_payload_accepts_objects_and_ids():
    client = MagicMock()
    client.execute.side_effect = _echo_results
    reviewer = SimpleNamespace(uid="reviewer-id", name="REVIEWER")

    _organization(client).invite_users(
        ["ana@x.com"],
        reviewer,
        projects=[SimpleNamespace(uid="project-1"), "project-2"],
        user_groups=[SimpleNamespace(id="group-1"), "group-2"],
    )

    data = client.execute.call_args.args[1]["data"]
    assert data["workspaceWide"] is False
    assert data["roleId"] == "reviewer-id"
    assert data["projectIds"] == ["project-1", "project-2"]
    assert data["groupIds"] == ["group-1", "group-2"]


def test_invite_users_sends_requests_of_100_and_keeps_order():
    client = MagicMock()
    client.execute.side_effect = _echo_results
    emails = [f"user{index}@x.com" for index in range(230)]
    labeler = SimpleNamespace(uid="labeler-id", name="LABELER")

    results = _organization(client).invite_users(emails, labeler)

    sizes = [
        len(call.args[1]["data"]["emails"])
        for call in client.execute.call_args_list
    ]
    assert sizes == [100, 100, 30]
    assert [result.email for result in results] == emails


def test_invite_users_parses_reasons_and_unknown_statuses():
    client = MagicMock()
    client.execute.return_value = {
        "inviteMembers": {
            "results": [
                {
                    "email": "grp@x.com",
                    "status": "NOT_ALLOWED",
                    "reason": "GROUP_ACCESS",
                    "inviteId": None,
                },
                {
                    "email": "new@x.com",
                    "status": "SOMETHING_NEW",
                    "reason": None,
                    "inviteId": None,
                },
            ]
        }
    }
    labeler = SimpleNamespace(uid="labeler-id", name="LABELER")

    results = _organization(client).invite_users(
        ["grp@x.com", "new@x.com"], labeler, projects=["project-1"]
    )

    assert results[0].status is InviteMemberStatus.NOT_ALLOWED
    assert results[0].reason == "GROUP_ACCESS"
    assert results[1].status == "SOMETHING_NEW"


def test_invite_users_rejects_an_empty_list():
    labeler = SimpleNamespace(uid="labeler-id", name="LABELER")
    with pytest.raises(ValueError):
        _organization(MagicMock()).invite_users([], labeler)


def test_invite_users_rejects_workspace_wide_none_role():
    client = MagicMock()
    none_role = SimpleNamespace(uid="none-id", name="NONE")

    with pytest.raises(ValueError):
        _organization(client).invite_users(["ana@x.com"], none_role)
    client.execute.assert_not_called()


def test_invite_users_rejects_a_single_string():
    labeler = SimpleNamespace(uid="labeler-id", name="LABELER")
    with pytest.raises(ValueError):
        _organization(MagicMock()).invite_users("ana@x.com", labeler)


def test_invite_users_keeps_an_over_long_address_out_of_the_batch():
    client = MagicMock()
    client.execute.side_effect = _echo_results
    long_address = "a" * 321
    labeler = SimpleNamespace(uid="labeler-id", name="LABELER")

    results = _organization(client).invite_users(
        ["ana@x.com", long_address, " " + long_address], labeler
    )

    sent = client.execute.call_args.args[1]["data"]["emails"]
    assert sent == ["ana@x.com"]
    assert results[0].status is InviteMemberStatus.INVITED
    assert results[1] == InviteResult(
        long_address, InviteMemberStatus.INVALID_EMAIL, None, None
    )
    assert results[2].status is InviteMemberStatus.DUPLICATE


def test_invite_users_sends_a_valid_address_hidden_by_padding():
    client = MagicMock()
    client.execute.side_effect = _echo_results
    padded = "ana@x.com" + (" " * 320)
    labeler = SimpleNamespace(uid="labeler-id", name="LABELER")

    results = _organization(client).invite_users(
        [padded, "bob@x.com", "ana@x.com"], labeler
    )

    sent = client.execute.call_args.args[1]["data"]["emails"]
    assert sent == ["ana@x.com", "bob@x.com"]
    assert results[0].status is InviteMemberStatus.INVITED
    assert results[0].email == "ana@x.com"
    assert results[1].email == "bob@x.com"
    assert results[2].status is InviteMemberStatus.DUPLICATE


def test_invite_users_answers_repeats_across_requests_as_duplicates():
    client = MagicMock()
    client.execute.side_effect = _echo_results
    emails = [f"user{index}@x.com" for index in range(100)] + [" USER0@x.com"]
    labeler = SimpleNamespace(uid="labeler-id", name="LABELER")

    results = _organization(client).invite_users(emails, labeler)

    assert client.execute.call_count == 1
    assert len(results) == 101
    assert results[-1] == InviteResult(
        "user0@x.com", InviteMemberStatus.DUPLICATE, None, None
    )
