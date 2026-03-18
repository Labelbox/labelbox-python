import logging
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from labelbox.schema.issue import Issue, IssueStatus
from labelbox.schema.issue_category import IssueCategory
from labelbox.schema.issue_position import (
    ImageIssuePosition,
    PdfIssuePosition,
    VideoFrameRange,
    VideoIssuePosition,
    _deserialize_position,
)
from labelbox.schema.project import Project

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


def _project_field_values(media_type="IMAGE"):
    """Minimal field values needed to construct a ``Project`` DbObject."""
    return {
        "id": "proj-1",
        "name": "Test Project",
        "description": "",
        "updatedAt": _NOW,
        "createdAt": _NOW,
        "setupComplete": None,
        "lastActivityTime": None,
        "autoAuditNumberOfLabels": 1,
        "autoAuditPercentage": 0.0,
        "allowedMediaType": media_type,
        "editorTaskType": None,
        "dataRowCount": 0,
        "modelSetupComplete": None,
        "uploadType": None,
        "isBenchmarkEnabled": False,
        "isConsensusEnabled": False,
        # Relationships with cache=True need a value
        "ontology": {"id": "onto-1", "name": "test", "normalized": "{}"},
    }


def _make_project(client=None, media_type="IMAGE"):
    c = client or _make_client()
    return Project(c, _project_field_values(media_type))


# ---------------------------------------------------------------------------
# create_issue
# ---------------------------------------------------------------------------


class TestCreateIssue:
    def test_basic(self):
        client = _make_client()
        project = _make_project(client)
        client.execute.return_value = {"createIssue": _ISSUE_RAW}

        issue = project.create_issue(
            content="Something is wrong",
            data_row_id="dr-1",
        )
        assert isinstance(issue, Issue)
        assert issue.id == "issue-1"
        args, _ = client.execute.call_args
        assert "CreateIssuePyApi" in args[0]
        data = args[1]["data"]
        assert data["content"] == "Something is wrong"
        assert data["projectId"] == "proj-1"
        assert data["dataRowId"] == "dr-1"
        assert data["type"] == "Issue"

    def test_with_label_and_category(self):
        client = _make_client()
        project = _make_project(client)
        client.execute.return_value = {"createIssue": _ISSUE_RAW}

        project.create_issue(
            content="Issue",
            data_row_id="dr-1",
            label_id="label-1",
            category_id="cat-1",
        )
        args, _ = client.execute.call_args
        data = args[1]["data"]
        assert data["labelId"] == "label-1"
        assert data["categoryId"] == "cat-1"

    def test_with_image_position(self):
        client = _make_client()
        project = _make_project(client, media_type="IMAGE")
        client.execute.return_value = {"createIssue": _ISSUE_RAW}

        pos = ImageIssuePosition(x=100, y=200)
        project.create_issue(
            content="Pin here",
            data_row_id="dr-1",
            position=pos,
        )
        args, _ = client.execute.call_args
        data = args[1]["data"]
        assert data["position"] == {"type": "Point", "coordinates": [100, 200]}

    def test_position_validation_wrong_type(self):
        client = _make_client()
        project = _make_project(client, media_type="IMAGE")

        with pytest.raises(TypeError, match="PdfIssuePosition"):
            project.create_issue(
                content="Wrong position",
                data_row_id="dr-1",
                position=PdfIssuePosition(x=0.5, y=0.5, page=0),
            )

    def test_accepts_datarow_object(self):
        client = _make_client()
        project = _make_project(client)
        client.execute.return_value = {"createIssue": _ISSUE_RAW}

        mock_dr = SimpleNamespace(uid="dr-obj-1")
        project.create_issue(content="Test", data_row_id=mock_dr)
        args, _ = client.execute.call_args
        assert args[1]["data"]["dataRowId"] == "dr-obj-1"

    def test_accepts_label_object(self):
        client = _make_client()
        project = _make_project(client)
        client.execute.return_value = {"createIssue": _ISSUE_RAW}

        mock_label = SimpleNamespace(uid="label-obj-1")
        project.create_issue(
            content="Test",
            data_row_id="dr-1",
            label_id=mock_label,
        )
        args, _ = client.execute.call_args
        assert args[1]["data"]["labelId"] == "label-obj-1"

    def test_accepts_category_object(self):
        client = _make_client()
        project = _make_project(client)
        client.execute.return_value = {"createIssue": _ISSUE_RAW}

        mock_cat = SimpleNamespace(uid="cat-obj-1")
        project.create_issue(
            content="Test",
            data_row_id="dr-1",
            category_id=mock_cat,
        )
        args, _ = client.execute.call_args
        assert args[1]["data"]["categoryId"] == "cat-obj-1"

    def test_no_position_validation_when_media_type_none(self):
        """Projects with unknown media type should not raise on position."""
        client = _make_client()
        project = _make_project(client, media_type=None)
        client.execute.return_value = {"createIssue": _ISSUE_RAW}

        pos = ImageIssuePosition(x=10, y=20)
        project.create_issue(
            content="Test",
            data_row_id="dr-1",
            position=pos,
        )
        # No error means success

    def test_video_position_on_video_project(self):
        client = _make_client()
        project = _make_project(client, media_type="VIDEO")
        client.execute.return_value = {"createIssue": _ISSUE_RAW}

        pos = VideoIssuePosition(
            frames=[VideoFrameRange(start=5, end=5, x=100, y=200)]
        )
        project.create_issue(
            content="Video issue",
            data_row_id="dr-1",
            position=pos,
        )
        args, _ = client.execute.call_args
        assert args[1]["data"]["position"]["type"] == "KeyframesGeoJSONPoint"


# ---------------------------------------------------------------------------
# get_issues
# ---------------------------------------------------------------------------


class TestGetIssues:
    def test_returns_paginated_collection(self):
        client = _make_client()
        project = _make_project(client)
        result = project.get_issues()
        # PaginatedCollection is returned (lazy); no execute call yet
        from labelbox.pagination import PaginatedCollection

        assert isinstance(result, PaginatedCollection)

    def test_with_status_filter(self):
        client = _make_client()
        project = _make_project(client)
        result = project.get_issues(status=IssueStatus.OPEN)
        # The params should contain the status filter
        assert result.paginator.params["where"]["status"] == "Open"

    def test_with_data_row_filter(self):
        client = _make_client()
        project = _make_project(client)
        result = project.get_issues(data_row_id="dr-1")
        assert result.paginator.params["where"]["dataRow"] == {"id": "dr-1"}


# ---------------------------------------------------------------------------
# get_issue
# ---------------------------------------------------------------------------


class TestGetIssue:
    def test_get_single_issue(self):
        client = _make_client()
        project = _make_project(client)
        client.execute.return_value = {"issue": _ISSUE_RAW}

        issue = project.get_issue("issue-1")
        assert issue.id == "issue-1"
        args, _ = client.execute.call_args
        assert "GetIssuePyApi" in args[0]
        assert args[1]["where"] == {"id": "issue-1"}


# ---------------------------------------------------------------------------
# delete_issues
# ---------------------------------------------------------------------------


class TestDeleteIssues:
    def test_delete_single(self):
        client = _make_client()
        project = _make_project(client)
        client.execute.return_value = {"deleteIssue": {"id": "issue-1"}}

        assert project.delete_issues(["issue-1"]) is True
        args, _ = client.execute.call_args
        assert "DeleteIssuePyApi" in args[0]
        assert args[1]["data"]["issueIds"] == ["issue-1"]

    def test_delete_multiple(self):
        client = _make_client()
        project = _make_project(client)
        client.execute.return_value = {"deleteIssue": {"id": "issue-1"}}

        assert project.delete_issues(["issue-1", "issue-2"]) is True
        args, _ = client.execute.call_args
        assert args[1]["data"]["issueIds"] == ["issue-1", "issue-2"]


# ---------------------------------------------------------------------------
# create_issue_category
# ---------------------------------------------------------------------------


class TestCreateIssueCategory:
    def test_create(self):
        client = _make_client()
        project = _make_project(client)
        client.execute.return_value = {
            "createIssueCategory": {
                "id": "cat-1",
                "name": "Quality",
                "description": "Quality issues",
            }
        }

        cat = project.create_issue_category(
            name="Quality", description="Quality issues"
        )
        assert isinstance(cat, IssueCategory)
        assert cat.id == "cat-1"
        assert cat.name == "Quality"
        args, _ = client.execute.call_args
        assert "CreateIssueCategoryPyApi" in args[0]
        assert args[1]["data"]["projectId"] == "proj-1"


# ---------------------------------------------------------------------------
# get_issue_categories
# ---------------------------------------------------------------------------


class TestGetIssueCategories:
    def test_get_categories(self):
        client = _make_client()
        project = _make_project(client)
        client.execute.return_value = {
            "project": {
                "issueCategories": [
                    {
                        "id": "cat-1",
                        "name": "Quality",
                        "description": "Quality issues",
                    },
                    {
                        "id": "cat-2",
                        "name": "Labeling",
                        "description": "Labeling issues",
                    },
                ]
            }
        }

        cats = project.get_issue_categories()
        assert len(cats) == 2
        assert cats[0].name == "Quality"
        assert cats[1].name == "Labeling"

    def test_empty_categories(self):
        client = _make_client()
        project = _make_project(client)
        client.execute.return_value = {"project": {"issueCategories": []}}

        cats = project.get_issue_categories()
        assert cats == []


# ---------------------------------------------------------------------------
# _deserialize_position fallback
# ---------------------------------------------------------------------------


class TestDeserializePositionFallback:
    def test_unrecognized_returns_none_and_warns(self, caplog):
        raw = {"totally": "unknown", "structure": True}
        with caplog.at_level(logging.WARNING):
            result = _deserialize_position(raw)
        assert result is None
        assert "Unrecognized issue position structure" in caplog.text
