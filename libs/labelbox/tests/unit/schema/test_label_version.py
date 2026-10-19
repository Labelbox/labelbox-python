from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from labelbox import LabelVersion, LabelVersionAction, LabelVersionStage
from labelbox.schema import label_version
from labelbox.schema.label import Label
from labelbox.schema.project import Project

PROJECT_ID = "cproject000000000000000001"


def node(index, **overrides):
    return {
        "id": f"cversion00000000000000000{index}",
        "labelId": "clabel0000000000000000001",
        "dataRowId": "cdatarow00000000000000001",
        "projectId": PROJECT_ID,
        "action": "SUBMITTED",
        "createdAt": f"2026-10-19T10:00:0{index}.000Z",
        "createdById": "clabeler000000000000000001",
        "stage": {
            "taskQueueId": "b1a2c3d4-0000-0000-0000-000000000001",
            "name": "Initial labeling task",
            "type": "INITIAL_LABELING_QUEUE",
        },
        "annotationCount": 1,
        "label": '{"objects":[],"classifications":[{"title":"Caption"}]}',
        "labelJson": {
            "objects": [],
            "classifications": [{"title": "Caption"}],
        },
        **overrides,
    }


def client_returning(*pages):
    """A client whose execute answers with ``pages`` in turn and keeps a copy
    of each call's params in ``client.sent`` (the paginator reuses one dict)."""
    client = MagicMock()
    client.sent = []
    answers = list(pages)

    def execute(query, params, **_):
        client.sent.append((query, dict(params)))
        return answers.pop(0)

    client.execute.side_effect = execute
    return client


def page(nodes, next_cursor=None):
    return {"labelVersions": {"nodes": nodes, "nextCursor": next_cursor}}


class TestGetLabelVersions:
    def test_pages_by_cursor_and_parses_versions(self):
        client = client_returning(
            page([node(1), node(2)], "cursor-1"),
            page([node(3, action="APPROVED", stage=None)]),
        )

        versions = list(
            label_version.get_label_versions(client, PROJECT_ID, page_size=2)
        )

        assert [v.id for v in versions] == [
            "cversion000000000000000001",
            "cversion000000000000000002",
            "cversion000000000000000003",
        ]
        first = versions[0]
        assert isinstance(first, LabelVersion)
        assert first.action is LabelVersionAction.SUBMITTED
        assert first.created_at == datetime(
            2026, 10, 19, 10, 0, 1, tzinfo=timezone.utc
        )
        assert first.created_by_id == "clabeler000000000000000001"
        assert first.stage == LabelVersionStage(
            task_queue_id="b1a2c3d4-0000-0000-0000-000000000001",
            name="Initial labeling task",
            type="INITIAL_LABELING_QUEUE",
        )
        assert first.label_json == {
            "objects": [],
            "classifications": [{"title": "Caption"}],
        }
        assert versions[2].stage is None
        assert versions[2].action is LabelVersionAction.APPROVED

        (query1, params1), (_, params2) = client.sent
        assert "labelVersions(where: $where, first: $first, after: $from)" in (
            query1
        )
        assert "label labelJson" in query1
        assert params1 == {
            "where": {"projectId": PROJECT_ID},
            "first": 2,
            "from": None,
        }
        assert params2["from"] == "cursor-1"

    def test_sends_only_the_filters_given(self):
        client = client_returning(page([]))
        label = SimpleNamespace(uid="clabel0000000000000000001")
        user = SimpleNamespace(uid="creviewer0000000000000001")

        list(
            label_version.get_label_versions(
                client,
                PROJECT_ID,
                label=label,
                data_row="cdatarow00000000000000001",
                created_by=user,
                created_after=datetime(2026, 10, 1),
                created_before="2026-11-01T02:00:00+02:00",
            )
        )

        [(_, params)] = client.sent
        assert params["where"] == {
            "projectId": PROJECT_ID,
            "labelId": "clabel0000000000000000001",
            "dataRowId": "cdatarow00000000000000001",
            "createdById": "creviewer0000000000000001",
            "createdAfter": "2026-10-01T00:00:00.000Z",
            "createdBefore": "2026-11-01T00:00:00.000Z",
        }
        assert params["first"] == 100

    def test_can_leave_annotations_out(self):
        client = client_returning(
            page(
                [
                    {
                        k: v
                        for k, v in node(1).items()
                        if k not in ("label", "labelJson")
                    }
                ]
            )
        )

        [version] = list(
            label_version.get_label_versions(
                client, PROJECT_ID, include_annotations=False
            )
        )

        [(query, _)] = client.sent
        assert "labelJson" not in query
        assert version.label is None
        assert version.label_json is None

    def test_keeps_an_unknown_action_as_a_string(self):
        client = client_returning(page([node(1, action="NEW_ACTION")]))

        [version] = list(label_version.get_label_versions(client, PROJECT_ID))

        assert version.action == "NEW_ACTION"

    def test_parses_label_json_sent_as_text(self):
        client = client_returning(page([node(1, labelJson='{"objects": []}')]))

        [version] = list(label_version.get_label_versions(client, PROJECT_ID))

        assert version.label_json == {"objects": []}

    @pytest.mark.parametrize("page_size", [0, 101, "10"])
    def test_refuses_a_bad_page_size(self, page_size):
        with pytest.raises(ValueError, match="page_size"):
            label_version.get_label_versions(
                MagicMock(), PROJECT_ID, page_size=page_size
            )

    def test_refuses_an_empty_time_range(self):
        with pytest.raises(ValueError, match="created_after must be before"):
            label_version.get_label_versions(
                MagicMock(),
                PROJECT_ID,
                created_after="2026-11-01T00:00:00Z",
                created_before="2026-10-01T00:00:00Z",
            )

    def test_refuses_an_unreadable_time(self):
        with pytest.raises(ValueError, match="created_after"):
            label_version.get_label_versions(
                MagicMock(), PROJECT_ID, created_after="last tuesday"
            )

    def test_refuses_an_empty_id(self):
        with pytest.raises(ValueError, match="label"):
            label_version.get_label_versions(MagicMock(), PROJECT_ID, label="")


class TestGetLabelVersion:
    def test_reads_one_version(self):
        client = MagicMock()
        client.execute.return_value = {"labelVersion": node(1, action="SAVED")}

        version = label_version.get_label_version(
            client, "cversion000000000000000001"
        )

        assert version is not None
        assert version.action is LabelVersionAction.SAVED
        (query, params), _ = client.execute.call_args
        assert "labelVersion(where: { id: $id })" in query
        assert params == {"id": "cversion000000000000000001"}

    def test_returns_none_when_unreadable(self):
        client = MagicMock()
        client.execute.return_value = {"labelVersion": None}

        assert label_version.get_label_version(client, "cmissing") is None


class TestEntryPoints:
    def test_project_label_versions(self):
        client = client_returning(page([node(1)]))
        project = Project(client, {"id": PROJECT_ID, **_project_fields()})

        versions = list(
            project.label_versions(label="clabel0000000000000000001")
        )

        assert len(versions) == 1
        [(_, params)] = client.sent
        assert params["where"] == {
            "projectId": PROJECT_ID,
            "labelId": "clabel0000000000000000001",
        }

    def test_label_versions(self):
        client = client_returning(page([node(1)]))
        label = Label(
            client, {"id": "clabel0000000000000000001", **_label_fields()}
        )
        # The relationship is per instance; the label's project is one read.
        label.project = lambda: SimpleNamespace(uid=PROJECT_ID)

        versions = list(label.versions(include_annotations=False))

        assert len(versions) == 1
        [(query, params)] = client.sent
        assert params["where"] == {
            "projectId": PROJECT_ID,
            "labelId": "clabel0000000000000000001",
        }
        assert "labelJson" not in query

    def test_client_get_label_version(self):
        from labelbox import Client

        client = MagicMock(spec=Client)
        client.execute.return_value = {"labelVersion": node(1)}

        version = Client.get_label_version(client, "cversion000000000000000001")

        assert version is not None and version.label_id == (
            "clabel0000000000000000001"
        )


def _project_fields():
    return {
        field.graphql_name: None
        for field in Project.fields()
        if field.graphql_name != "id"
    }


def _label_fields():
    return {
        field.graphql_name: None
        for field in Label.fields()
        if field.graphql_name != "id"
    }
