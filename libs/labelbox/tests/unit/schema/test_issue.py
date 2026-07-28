from unittest.mock import MagicMock

from labelbox.schema.issue import (
    Comment,
    IssueStatus,
    _parse_comment,
    _parse_issue,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NOW = "2025-01-15T10:00:00.000Z"

_USER_RAW = {
    "id": "user-1",
    "email": "alice@example.com",
    "nickname": "alice",
    "name": "Alice",
    "picture": "",
    "isViewer": False,
    "isExternalUser": False,
    "createdAt": _NOW,
    "updatedAt": _NOW,
    "lastLoginAt": _NOW,
}

_COMMENT_RAW = {
    "id": "comment-1",
    "content": "Looks good",
    "createdBy": _USER_RAW,
    "createdAt": _NOW,
    "updatedAt": _NOW,
}

_ISSUE_RAW = {
    "id": "issue-1",
    "friendlyId": "I-42",
    "labelId": "label-1",
    "dataRowId": "dr-1",
    "categoryId": "cat-1",
    "content": "Something is wrong",
    "position": None,
    "status": "Open",
    "createdBy": _USER_RAW,
    "resolvedBy": None,
    "createdAt": _NOW,
    "updatedAt": _NOW,
    "resolvedAt": None,
    "contentUpdatedAt": None,
    "latestReplyAt": None,
}


def _make_client():
    return MagicMock()


def _make_issue(client=None, overrides=None, project_id="proj-1"):
    c = client or _make_client()
    raw = {**_ISSUE_RAW, **(overrides or {})}
    return _parse_issue(c, raw, project_id=project_id)


def _make_comment(client=None):
    c = client or _make_client()
    return _parse_comment(c, _COMMENT_RAW)


# ---------------------------------------------------------------------------
# _parse_issue / _parse_comment
# ---------------------------------------------------------------------------


class TestParseIssue:
    def test_basic_fields(self):
        issue = _make_issue()
        assert issue.id == "issue-1"
        assert issue.friendly_id == "I-42"
        assert issue.content == "Something is wrong"
        assert issue.status == IssueStatus.OPEN
        assert issue.data_row_id == "dr-1"
        assert issue.label_id == "label-1"
        assert issue.category_id == "cat-1"
        assert issue.position is None

    def test_created_by_is_user(self):
        issue = _make_issue()
        # User DbObject has .uid
        assert issue.created_by.uid == "user-1"

    def test_resolved_by_none(self):
        issue = _make_issue()
        assert issue.resolved_by is None

    def test_resolved_by_present(self):
        issue = _make_issue(overrides={"resolvedBy": _USER_RAW})
        assert issue.resolved_by.uid == "user-1"


class TestParseComment:
    def test_basic_fields(self):
        comment = _make_comment()
        assert comment.id == "comment-1"
        assert comment.content == "Looks good"
        assert comment.created_by.uid == "user-1"


# ---------------------------------------------------------------------------
# Issue mutation methods
# ---------------------------------------------------------------------------


class TestIssueUpdate:
    def test_update_content(self):
        client = _make_client()
        issue = _make_issue(client)
        client.execute.return_value = {
            "updateIssue": {**_ISSUE_RAW, "content": "Updated"}
        }
        updated = issue.update(content="Updated")
        assert updated.content == "Updated"
        # Verify GraphQL call
        args, _ = client.execute.call_args
        assert "UpdateIssuePyApi" in args[0]
        assert args[1]["data"]["content"] == "Updated"

    def test_update_no_args_returns_self(self):
        client = _make_client()
        issue = _make_issue(client)
        result = issue.update()
        assert result is issue
        client.execute.assert_not_called()


class TestIssueDelete:
    def test_delete(self):
        client = _make_client()
        issue = _make_issue(client)
        client.execute.return_value = {"deleteIssue": {"id": "issue-1"}}
        assert issue.delete() is True
        args, _ = client.execute.call_args
        assert "DeleteIssuePyApi" in args[0]
        assert args[1]["data"]["issueIds"] == ["issue-1"]


class TestIssueResolve:
    def test_resolve(self):
        client = _make_client()
        issue = _make_issue(client)
        client.execute.return_value = {
            "resolveIssue": {**_ISSUE_RAW, "status": "Resolved"}
        }
        resolved = issue.resolve()
        assert resolved.status == IssueStatus.RESOLVED
        args, _ = client.execute.call_args
        assert "ResolveIssuePyApi" in args[0]


class TestIssueReopen:
    def test_reopen(self):
        client = _make_client()
        issue = _make_issue(client, overrides={"status": "Resolved"})
        client.execute.return_value = {
            "openIssue": {**_ISSUE_RAW, "status": "Open"}
        }
        reopened = issue.reopen()
        assert reopened.status == IssueStatus.OPEN
        args, _ = client.execute.call_args
        assert "OpenIssuePyApi" in args[0]


class TestIssueCreateComment:
    def test_create_comment(self):
        client = _make_client()
        issue = _make_issue(client)
        client.execute.return_value = {"createComment": _COMMENT_RAW}
        comment = issue.create_comment(content="Nice work")
        assert isinstance(comment, Comment)
        args, _ = client.execute.call_args
        assert "CreateCommentPyApi" in args[0]
        assert args[1]["data"]["content"] == "Nice work"
        assert args[1]["data"]["issueId"] == "issue-1"


# ---------------------------------------------------------------------------
# Issue accessor methods
# ---------------------------------------------------------------------------


class TestIssueComments:
    def test_comments(self):
        client = _make_client()
        issue = _make_issue(client)
        client.execute.return_value = {"issue": {"comments": [_COMMENT_RAW]}}
        comments = issue.comments()
        assert len(comments) == 1
        assert comments[0].id == "comment-1"

    def test_comments_empty(self):
        client = _make_client()
        issue = _make_issue(client)
        client.execute.return_value = {"issue": {"comments": []}}
        assert issue.comments() == []


class TestIssueDataRow:
    def test_data_row(self):
        client = _make_client()
        issue = _make_issue(client)
        mock_dr = MagicMock()
        client.get_data_row.return_value = mock_dr
        result = issue.data_row()
        assert result is mock_dr
        client.get_data_row.assert_called_once_with("dr-1")

    def test_data_row_none_when_no_id(self):
        client = _make_client()
        issue = _make_issue(client, overrides={"dataRowId": None})
        assert issue.data_row() is None
        client.get_data_row.assert_not_called()


class TestIssueCategory:
    def test_category(self):
        client = _make_client()
        issue = _make_issue(client)
        # category() queries project -> issueCategories and matches by id
        client.execute.return_value = {
            "project": {
                "issueCategories": [
                    {
                        "id": "cat-1",
                        "name": "Quality",
                        "description": "Quality issues",
                    }
                ]
            }
        }
        cat = issue.category()
        assert cat is not None
        assert cat.id == "cat-1"
        assert cat.name == "Quality"

    def test_category_none_when_no_id(self):
        client = _make_client()
        issue = _make_issue(client, overrides={"categoryId": None})
        assert issue.category() is None


class TestIssueLabel:
    def test_label(self):
        client = _make_client()
        issue = _make_issue(client)
        mock_label = MagicMock()
        client._get_single.return_value = mock_label
        result = issue.label()
        assert result is mock_label
        client._get_single.assert_called_once()

    def test_label_none_when_no_id(self):
        client = _make_client()
        issue = _make_issue(client, overrides={"labelId": None})
        assert issue.label() is None
        client._get_single.assert_not_called()


# ---------------------------------------------------------------------------
# Comment mutation methods
# ---------------------------------------------------------------------------


class TestCommentUpdate:
    def test_update(self):
        client = _make_client()
        comment = _make_comment(client)
        client.execute.return_value = {
            "updateComment": {**_COMMENT_RAW, "content": "Revised"}
        }
        updated = comment.update(content="Revised")
        assert updated.content == "Revised"
        args, _ = client.execute.call_args
        assert "UpdateCommentPyApi" in args[0]


class TestCommentDelete:
    def test_delete(self):
        client = _make_client()
        comment = _make_comment(client)
        client.execute.return_value = {"deleteComment": {"id": "comment-1"}}
        assert comment.delete() is True
        args, _ = client.execute.call_args
        assert "DeleteCommentPyApi" in args[0]
