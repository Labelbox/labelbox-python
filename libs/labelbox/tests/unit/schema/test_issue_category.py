from unittest.mock import MagicMock

from labelbox.schema.issue_category import IssueCategory


def _make_client():
    return MagicMock()


def _make_category(client=None):
    c = client or _make_client()
    cat = IssueCategory(
        id="cat-1",
        name="Quality",
        description="Quality issues",
    )
    cat._client = c
    return cat


class TestIssueCategoryUpdate:
    def test_update(self):
        client = _make_client()
        cat = _make_category(client)
        client.execute.return_value = {
            "editIssueCategory": {
                "id": "cat-1",
                "name": "Renamed",
                "description": "New desc",
            }
        }
        updated = cat.update(name="Renamed", description="New desc")
        assert updated.name == "Renamed"
        assert updated.description == "New desc"
        args, _ = client.execute.call_args
        assert "EditIssueCategoryPyApi" in args[0]
        assert args[1]["where"] == {"id": "cat-1"}
        assert args[1]["data"] == {
            "name": "Renamed",
            "description": "New desc",
        }


class TestIssueCategoryDelete:
    def test_delete(self):
        client = _make_client()
        cat = _make_category(client)
        client.execute.return_value = {"deleteIssueCategory": {"id": "cat-1"}}
        assert cat.delete() is True
        args, _ = client.execute.call_args
        assert "DeleteIssueCategoryPyApi" in args[0]
        assert args[1]["where"] == {"id": "cat-1"}
