from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import requests
from google.api_core import retry
from lbox.exceptions import (
    ApiLimitError,
    AuthenticationError,
    AuthorizationError,
    InternalServerError,
    InvalidQueryError,
    LabelboxError,
    NetworkError,
    ResourceNotFoundError,
    TimeoutError,
)

from labelbox import (
    Client,
    PerformanceDeletedLabels,
    PerformanceInterval,
    PerformanceMemberType,
    PerformanceScoreBucket,
    PerformanceTimeBucket,
    Project,
)
from labelbox.schema import performance
from labelbox.schema.user_group import UserGroup

BASE = "https://api.labelbox.com/api/v1/performance"

# The schedule the SDK ships with. The tests below swap in a quick one.
SHIPPED_RETRY = performance._retry_transient

# Responses as the REST API returns them.
SERIES = {
    "projectId": "project-1",
    "metric": "labels_created",
    "unit": "count",
    "bucketType": "time",
    "buckets": [
        {
            "start": "2026-01-01T00:00:00.000Z",
            "end": "2026-01-02T00:00:00.000Z",
            "value": 4,
            "numerator": None,
            "denominator": None,
            "modes": None,
        }
    ],
    "interval": "day",
    "startDate": "2026-01-01",
    "endDate": "2026-01-07",
    "generatedAt": "2026-01-08T09:30:00.000Z",
}


def labeler(user_id):
    return {
        "userId": user_id,
        "projectId": "project-1",
        "email": f"{user_id}@example.com",
        "labelsCreated": 12,
        "labelsSkipped": 1,
        "memberTotalTime": 3600,
        "labelingTimeSubmitted": 3000,
        "labelingTimeSkipped": 100,
        "reviewsReceived": 4,
        "reviewTimeAll": 300,
        "reworkTimeAll": 200,
        "avgTimePerLabel": 250,
        "avgReviewTimeAll": 75,
        "avgReworkTimeAll": 50,
        "avgBenchmarkAgreement": 0.9,
        "avgConsensusAgreement": 0.8,
        "reworkPercentage": 0.1,
        "approvalPercentage": 0.9,
        "avgRating": 4.5,
        "isRemoved": False,
    }


def table(rows, total, page=1, cached_at=None):
    return {
        "projectId": "project-1",
        "data": rows,
        "page": page,
        "perPage": 50,
        "total": total,
        "startDate": "2026-01-01",
        "endDate": "2026-01-07",
        "cachedAt": cached_at,
        "generatedAt": "2026-01-08T09:30:00.000Z",
    }


REVIEWER = {
    "userId": "user-9",
    "projectId": "project-1",
    "email": "user-9@example.com",
    "labelsReviewed": 20,
    "labelsReworked": 2,
    "memberTotalTime": 1800,
    "avgReviewTime": 60,
    "avgReworkTime": 30,
    "reviewTime": 1200,
    "reworkTime": 600,
    "reworkPercentage": 0.1,
    "approvalPercentage": 0.9,
    "isRemoved": False,
}


def workspace_labeler(user_id, project_id, **fields):
    return {
        **{k: v for k, v in labeler(user_id).items() if k != "avgRating"},
        "projectId": project_id,
        "memberType": "internal",
        "projectName": "Project one",
        "projectOrganizationId": "org-1",
        "projectOrganizationName": "Org one",
        "isProjectDeleted": False,
        **fields,
    }


def workspace_table(rows, total, page=1, cached_at=None):
    return {
        "organizationId": "org-1",
        "projectIds": None,
        "ownerOrganizationIds": None,
        "memberType": None,
        "data": rows,
        "page": page,
        "perPage": 50,
        "total": total,
        "cachedAt": cached_at,
        "startDate": "2026-01-01",
        "endDate": "2026-01-07",
        "generatedAt": "2026-01-08T09:30:00.000Z",
    }


def response(body, status=200):
    reply = Mock()
    reply.status_code = status
    reply.json.return_value = body
    reply.text = str(body)
    return reply


@pytest.fixture(autouse=True)
def quick_retries(monkeypatch):
    # The real schedule waits seconds between attempts, for up to two minutes.
    monkeypatch.setattr(
        performance,
        "_retry_transient",
        retry.Retry(
            predicate=retry.if_exception_type(
                InternalServerError, TimeoutError
            ),
            initial=0.001,
            maximum=0.001,
            deadline=0.05,
        ),
    )


@pytest.fixture
def client():
    client = Client(api_key="api_key")
    client.connection.get = Mock(return_value=response(SERIES))
    return client


@pytest.fixture
def project(client):
    # The methods only read the project's client and ID.
    return SimpleNamespace(client=client, uid="project-1")


def sent(client, call=-1):
    """The URL and query string of a request the client made."""
    args, kwargs = client.connection.get.call_args_list[call]
    return args[0], kwargs["params"]


class TestMetricCatalog:
    def test_lists_the_metrics(self, client):
        client.connection.get.return_value = response(
            {
                "data": [
                    {
                        "name": "labels_created",
                        "category": "throughput",
                        "unit": "count",
                        "buckets": "time",
                        "description": "Labels created in the period.",
                    }
                ]
            }
        )

        metrics = client.get_performance_metrics()

        assert sent(client) == (f"{BASE}/metrics", {})
        assert [metric.name for metric in metrics] == ["labels_created"]
        assert metrics[0].unit == "count"
        assert metrics[0].description == "Labels created in the period."


class TestProjectMetric:
    def test_asks_for_the_metric_over_the_period(self, client, project):
        Project.get_performance_metric(
            project, "labels_created", "2026-01-01", "2026-01-07"
        )

        url, params = sent(client)
        assert url == f"{BASE}/projects/project-1/metrics/labels_created"
        assert params == {
            "startDate": "2026-01-01",
            "endDate": "2026-01-07",
            "interval": "day",
            "deletedLabels": "include",
        }

    def test_returns_a_value_per_interval(self, client, project):
        series = Project.get_performance_metric(
            project, "labels_created", "2026-01-01", "2026-01-07"
        )

        assert series.metric == "labels_created"
        assert series.unit == "count"
        assert series.bucket_type == "time"
        assert series.project_id == "project-1"
        assert series.start_date == date(2026, 1, 1)
        assert series.end_date == date(2026, 1, 7)
        assert series.generated_at == datetime(
            2026, 1, 8, 9, 30, tzinfo=timezone.utc
        )
        (bucket,) = series.buckets
        assert isinstance(bucket, PerformanceTimeBucket)
        assert bucket.start == datetime(2026, 1, 1, tzinfo=timezone.utc)
        assert bucket.end == datetime(2026, 1, 2, tzinfo=timezone.utc)
        assert bucket.value == 4
        assert bucket.modes is None

    def test_returns_score_ranges_for_a_distribution(self, client, project):
        client.connection.get.return_value = response(
            {
                **SERIES,
                "metric": "consensus_distribution",
                "bucketType": "score",
                "buckets": [
                    {"rangeStart": 0, "rangeEnd": 10, "value": 3},
                    {"rangeStart": 10, "rangeEnd": 20, "value": 9},
                ],
            }
        )

        series = Project.get_performance_metric(
            project, "consensus_distribution", "2026-01-01", "2026-01-07"
        )

        assert series.bucket_type == "score"
        assert all(
            isinstance(bucket, PerformanceScoreBucket)
            for bucket in series.buckets
        )
        assert [
            (b.range_start, b.range_end, b.value) for b in series.buckets
        ] == [
            (0, 10, 3),
            (10, 20, 9),
        ]

    def test_carries_the_ratio_and_the_split_by_activity(self, client, project):
        client.connection.get.return_value = response(
            {
                **SERIES,
                "metric": "aht_done_labels",
                "unit": "seconds",
                "buckets": [
                    {
                        "start": "2026-01-01T00:00:00.000Z",
                        "end": "2026-01-02T00:00:00.000Z",
                        "value": 90,
                        "numerator": 900,
                        "denominator": 10,
                        "modes": {
                            "creating": 60,
                            "reviewing": 20,
                            "reworking": 10,
                        },
                    }
                ],
            }
        )

        (bucket,) = Project.get_performance_metric(
            project, "aht_done_labels", "2026-01-01", "2026-01-07"
        ).buckets

        assert (bucket.value, bucket.numerator, bucket.denominator) == (
            90,
            900,
            10,
        )
        assert bucket.modes.creating == 60
        assert bucket.modes.reviewing == 20
        assert bucket.modes.reworking == 10

    def test_sends_the_filters(self, client, project):
        Project.get_performance_metric(
            project,
            "labels_created",
            "2026-01-01",
            "2026-01-07",
            interval=PerformanceInterval.WEEK,
            user_ids=["user-1", "user-2"],
            user_group_ids=["group-a"],
            batch_ids=["batch-1"],
            deleted_labels=PerformanceDeletedLabels.EXCLUDE,
        )

        _, params = sent(client)
        assert params == {
            "startDate": "2026-01-01",
            "endDate": "2026-01-07",
            "interval": "week",
            "userIds": "user-1,user-2",
            "userGroupIds": "group-a",
            "batchIds": "batch-1",
            "deletedLabels": "exclude",
        }

    def test_takes_plain_strings_in_place_of_the_enums(self, client, project):
        Project.get_performance_metric(
            project,
            "labels_created",
            "2026-01-01",
            "2026-01-07",
            interval="month",
            deleted_labels="only",
        )

        _, params = sent(client)
        assert params["interval"] == "month"
        assert params["deletedLabels"] == "only"

    def test_accepts_sdk_objects_where_ids_are_expected(self, client, project):
        Project.get_performance_metric(
            project,
            "labels_created",
            "2026-01-01",
            "2026-01-07",
            user_ids=[SimpleNamespace(uid="user-1"), "user-2"],
            batch_ids="batch-1",
        )

        _, params = sent(client)
        assert params["userIds"] == "user-1,user-2"
        assert params["batchIds"] == "batch-1"

    def test_accepts_user_group_objects(self, client, project):
        # UserGroup is a pydantic model whose ID is `id`, not `uid`.
        groups = [
            UserGroup(client=client, id="group-a", name="Vendor A"),
            UserGroup(client=client, id="group-b", name="Vendor B"),
        ]

        Project.get_performance_metric(
            project,
            "labels_created",
            "2026-01-01",
            "2026-01-07",
            user_group_ids=groups,
        )

        _, params = sent(client)
        assert params["userGroupIds"] == "group-a,group-b"

    @pytest.mark.parametrize(
        "not_an_id",
        [42, None, SimpleNamespace(name="no id"), SimpleNamespace(id="")],
    )
    def test_refuses_a_filter_value_that_has_no_id(
        self, client, project, not_an_id
    ):
        with pytest.raises(TypeError, match="Expected an ID"):
            Project.get_performance_metric(
                project,
                "labels_created",
                "2026-01-01",
                "2026-01-07",
                user_ids=["user-1", not_an_id],
            )

        client.connection.get.assert_not_called()

    def test_leaves_an_empty_filter_out(self, client, project):
        Project.get_performance_metric(
            project, "labels_created", "2026-01-01", "2026-01-07", user_ids=[]
        )

        _, params = sent(client)
        assert "userIds" not in params

    @pytest.mark.parametrize(
        "day, expected",
        [
            ("2026-01-31", "2026-01-31"),
            (date(2026, 1, 31), "2026-01-31"),
            (datetime(2026, 1, 31, 23, 30), "2026-01-31"),
            # Reports follow UTC days: 23:30 at UTC-8 is already 1 February.
            (
                datetime(
                    2026, 1, 31, 23, 30, tzinfo=timezone(timedelta(hours=-8))
                ),
                "2026-02-01",
            ),
        ],
    )
    def test_sends_a_date_as_a_utc_day(self, client, project, day, expected):
        Project.get_performance_metric(project, "labels_created", day, day)

        _, params = sent(client)
        assert params["startDate"] == expected
        assert params["endDate"] == expected

    def test_keeps_an_id_from_changing_the_path(self, client, project):
        Project.get_performance_metric(
            project, "../../labelers", "2026-01-01", "2026-01-07"
        )

        url, _ = sent(client)
        assert url == f"{BASE}/projects/project-1/metrics/..%2F..%2Flabelers"

    def test_gives_the_request_a_timeout(self, client, project):
        Project.get_performance_metric(
            project, "labels_created", "2026-01-01", "2026-01-07"
        )

        assert client.connection.get.call_args.kwargs["timeout"] > 0

    def test_ignores_fields_added_to_the_response_later(self, client, project):
        client.connection.get.return_value = response(
            {**SERIES, "asOf": "2026-01-08T09:00:00.000Z"}
        )

        series = Project.get_performance_metric(
            project, "labels_created", "2026-01-01", "2026-01-07"
        )

        assert series.metric == "labels_created"


class TestProjectLabelers:
    def test_asks_for_nothing_until_the_rows_are_read(self, client, project):
        Project.get_labeler_performance(project, "2026-01-01", "2026-01-07")

        client.connection.get.assert_not_called()

    def test_returns_the_rows(self, client, project):
        client.connection.get.return_value = response(
            table([labeler("user-1"), labeler("user-2")], total=2)
        )

        rows = list(
            Project.get_labeler_performance(project, "2026-01-01", "2026-01-07")
        )

        url, params = sent(client)
        assert url == f"{BASE}/projects/project-1/labelers"
        assert params == {
            "startDate": "2026-01-01",
            "endDate": "2026-01-07",
            "deletedLabels": "include",
            "perPage": "50",
            "page": "1",
        }
        assert [row.user_id for row in rows] == ["user-1", "user-2"]
        first = rows[0]
        assert first.email == "user-1@example.com"
        assert first.labels_created == 12
        assert first.member_total_time == 3600
        assert first.avg_consensus_agreement == 0.8
        assert first.avg_rating == 4.5
        assert first.is_removed is False

    def test_fetches_page_after_page_until_it_has_every_row(
        self, client, project
    ):
        client.connection.get.side_effect = [
            response(table([labeler("user-1"), labeler("user-2")], total=5)),
            response(
                table([labeler("user-3"), labeler("user-4")], total=5, page=2)
            ),
            response(table([labeler("user-5")], total=5, page=3)),
        ]

        rows = list(
            Project.get_labeler_performance(
                project, "2026-01-01", "2026-01-07", page_size=2
            )
        )

        assert [row.user_id for row in rows] == [
            "user-1",
            "user-2",
            "user-3",
            "user-4",
            "user-5",
        ]
        pages = [
            sent(client, call)[1]["page"]
            for call in range(client.connection.get.call_count)
        ]
        assert pages == ["1", "2", "3"]
        assert sent(client)[1]["perPage"] == "2"

    def test_stops_if_a_page_comes_back_empty(self, client, project):
        # The table shrank while it was being read.
        client.connection.get.side_effect = [
            response(table([labeler("user-1")], total=3)),
            response(table([], total=3, page=2)),
        ]

        rows = list(
            Project.get_labeler_performance(project, "2026-01-01", "2026-01-07")
        )

        assert [row.user_id for row in rows] == ["user-1"]
        assert client.connection.get.call_count == 2

    def test_reads_the_total_and_cache_time_from_the_first_page_once(
        self, client, project
    ):
        client.connection.get.return_value = response(
            table(
                [labeler("user-1")],
                total=1,
                cached_at="2026-01-08T09:00:00.000Z",
            )
        )
        labelers = Project.get_labeler_performance(
            project, "2026-01-01", "2026-01-07"
        )

        assert labelers.total == 1
        assert labelers.cached_at == datetime(
            2026, 1, 8, 9, 0, tzinfo=timezone.utc
        )
        assert [row.user_id for row in labelers] == ["user-1"]
        assert client.connection.get.call_count == 1

    def test_has_no_cache_time_for_rows_computed_on_request(
        self, client, project
    ):
        client.connection.get.return_value = response(table([], total=0))

        labelers = Project.get_labeler_performance(
            project, "2026-01-01", "2026-01-07"
        )

        assert labelers.cached_at is None
        assert list(labelers) == []

    def test_sorts_by_an_attribute_of_the_row(self, client, project):
        client.connection.get.return_value = response(table([], total=0))

        list(
            Project.get_labeler_performance(
                project,
                "2026-01-01",
                "2026-01-07",
                sort_by="labels_created",
                descending=True,
            )
        )

        _, params = sent(client)
        assert params["sort"] == "labelsCreated"
        assert params["order"] == "desc"

    def test_sends_no_order_without_a_sort(self, client, project):
        client.connection.get.return_value = response(table([], total=0))

        list(
            Project.get_labeler_performance(
                project, "2026-01-01", "2026-01-07", descending=True
            )
        )

        _, params = sent(client)
        assert "sort" not in params
        assert "order" not in params

    def test_can_skip_the_cache(self, client, project):
        client.connection.get.return_value = response(table([], total=0))

        list(
            Project.get_labeler_performance(
                project, "2026-01-01", "2026-01-07", use_cache=False
            )
        )

        _, params = sent(client)
        assert params["useCache"] == "false"

    def test_filters_by_user_group(self, client, project):
        client.connection.get.return_value = response(table([], total=0))

        list(
            Project.get_labeler_performance(
                project,
                "2026-01-01",
                "2026-01-07",
                user_group_ids=["group-a", "group-b"],
            )
        )

        _, params = sent(client)
        assert params["userGroupIds"] == "group-a,group-b"


class TestProjectReviewers:
    def test_returns_the_rows(self, client, project):
        client.connection.get.return_value = response(
            table(
                [
                    {
                        "userId": "user-9",
                        "projectId": "project-1",
                        "email": "usr.email.user-9@internal.labelbox.com",
                        "labelsReviewed": 20,
                        "labelsReworked": 2,
                        "memberTotalTime": 1800,
                        "avgReviewTime": 60,
                        "avgReworkTime": 30,
                        "reviewTime": 1200,
                        "reworkTime": 600,
                        "reworkPercentage": 0.1,
                        "approvalPercentage": 0.9,
                        "isRemoved": True,
                    }
                ],
                total=1,
            )
        )

        (reviewer,) = list(
            Project.get_reviewer_performance(
                project,
                "2026-01-01",
                "2026-01-07",
                sort_by="labels_reviewed",
            )
        )

        url, params = sent(client)
        assert url == f"{BASE}/projects/project-1/reviewers"
        assert params["sort"] == "labelsReviewed"
        assert params["order"] == "asc"
        assert "useCache" not in params
        assert reviewer.labels_reviewed == 20
        assert reviewer.review_time == 1200
        assert reviewer.is_removed is True
        # Masked emails come through as the API returns them.
        assert reviewer.email == "usr.email.user-9@internal.labelbox.com"


class TestProjectReportDownload:
    def test_returns_the_link(self, client, project):
        client.connection.get.return_value = response(
            {
                "projectId": "project-1",
                "url": "https://files.example/report.csv",
                "expiresInSeconds": 86400,
                "startDate": "2026-01-01",
                "endDate": "2026-01-07",
                "generatedAt": "2026-01-08T09:30:00.000Z",
            }
        )

        report = Project.get_performance_report_download(
            project, "2026-01-01", "2026-01-07", user_group_ids=["group-a"]
        )

        url, params = sent(client)
        assert url == f"{BASE}/projects/project-1/download"
        assert params["userGroupIds"] == "group-a"
        assert report.url == "https://files.example/report.csv"
        assert report.expires_in_seconds == 86400
        assert report.start_date == date(2026, 1, 1)


class TestWorkspace:
    def test_returns_a_metric_across_the_workspace(self, client):
        client.connection.get.return_value = response(
            {
                **{k: v for k, v in SERIES.items() if k != "projectId"},
                "organizationId": "org-1",
                "projectIds": ["project-1", "project-2"],
            }
        )

        series = client.get_workspace_performance_metric(
            "labels_created",
            date(2026, 1, 1),
            date(2026, 1, 7),
            project_ids=["project-1", "project-2"],
            use_cache=False,
        )

        url, params = sent(client)
        assert url == f"{BASE}/workspace/metrics/labels_created"
        assert params == {
            "startDate": "2026-01-01",
            "endDate": "2026-01-07",
            "interval": "day",
            "projectIds": "project-1,project-2",
            "deletedLabels": "include",
            "useCache": "false",
        }
        assert series.organization_id == "org-1"
        assert series.project_ids == ["project-1", "project-2"]
        assert series.project_id is None

    def test_narrows_a_metric_by_member_type_and_owning_organization(
        self, client
    ):
        client.connection.get.return_value = response(
            {
                **{k: v for k, v in SERIES.items() if k != "projectId"},
                "organizationId": "org-1",
                "projectIds": None,
                "ownerOrganizationIds": ["org-2"],
                "memberType": "external",
            }
        )

        series = client.get_workspace_performance_metric(
            "labels_created",
            "2026-01-01",
            "2026-01-07",
            member_type=PerformanceMemberType.EXTERNAL,
            owner_organization_ids=["org-2"],
        )

        _, params = sent(client)
        assert params["memberType"] == "external"
        assert params["ownerOrganizationIds"] == "org-2"
        assert series.member_type == "external"
        assert series.owner_organization_ids == ["org-2"]

    def test_sends_neither_narrowing_unless_asked(self, client):
        client.get_workspace_performance_metric(
            "labels_created", "2026-01-01", "2026-01-07"
        )

        _, params = sent(client)
        assert "memberType" not in params
        assert "ownerOrganizationIds" not in params

    def test_returns_a_row_per_labeler_and_project(self, client):
        client.connection.get.return_value = response(
            workspace_table(
                [
                    workspace_labeler("user-1", "project-1"),
                    workspace_labeler(
                        "user-2",
                        "project-shared",
                        memberType="external",
                        projectOrganizationId="org-2",
                        projectOrganizationName="Org two",
                    ),
                ],
                total=2,
            )
        )

        rows = list(
            client.get_workspace_labeler_performance(
                "2026-01-01", "2026-01-07", user_ids=["user-1", "user-2"]
            )
        )

        url, params = sent(client)
        assert url == f"{BASE}/workspace/labelers"
        assert params == {
            "startDate": "2026-01-01",
            "endDate": "2026-01-07",
            "userIds": "user-1,user-2",
            "deletedLabels": "include",
            "perPage": "50",
            "page": "1",
        }
        assert [row.project_id for row in rows] == [
            "project-1",
            "project-shared",
        ]
        assert rows[0].project_name == "Project one"
        assert rows[0].labels_created == 12
        # Whose project it is, and whose member did the work.
        assert rows[0].project_organization_name == "Org one"
        assert rows[0].member_type == "internal"
        assert rows[1].project_organization_id == "org-2"
        assert rows[1].member_type == "external"

    def test_fetches_the_workspace_table_a_page_at_a_time(self, client):
        client.connection.get.side_effect = [
            response(
                workspace_table(
                    [
                        workspace_labeler("user-1", "project-1"),
                        workspace_labeler("user-2", "project-1"),
                    ],
                    total=3,
                    cached_at="2026-01-08T09:29:00.000Z",
                )
            ),
            response(
                workspace_table(
                    [workspace_labeler("user-3", "project-1")],
                    total=3,
                    page=2,
                )
            ),
        ]

        rows = client.get_workspace_labeler_performance(
            "2026-01-01", "2026-01-07", page_size=2
        )

        assert rows.total == 3
        assert rows.cached_at == datetime(
            2026, 1, 8, 9, 29, tzinfo=timezone.utc
        )
        assert [row.user_id for row in rows] == ["user-1", "user-2", "user-3"]
        assert [sent(client, call)[1]["page"] for call in (0, 1)] == ["1", "2"]
        assert sent(client)[1]["perPage"] == "2"

    def test_filters_and_sorts_the_workspace_table(self, client):
        client.connection.get.return_value = response(workspace_table([], 0))

        list(
            client.get_workspace_labeler_performance(
                "2026-01-01",
                "2026-01-07",
                project_ids=["project-1"],
                member_type="external",
                owner_organization_ids=["org-2", "org-3"],
                sort_by="avg_time_per_label",
                descending=True,
                use_cache=False,
            )
        )

        _, params = sent(client)
        assert params["projectIds"] == "project-1"
        assert params["memberType"] == "external"
        assert params["ownerOrganizationIds"] == "org-2,org-3"
        assert params["sort"] == "avgTimePerLabel"
        assert params["order"] == "desc"
        assert params["useCache"] == "false"

    def test_reads_a_row_whose_member_no_longer_exists(self, client):
        client.connection.get.return_value = response(
            workspace_table(
                [workspace_labeler("user-1", "project-1", memberType=None)], 1
            )
        )

        (row,) = client.get_workspace_labeler_performance(
            "2026-01-01", "2026-01-07"
        )

        assert row.member_type is None


class TestMemberType:
    def test_says_whose_member_each_labeler_and_reviewer_is(
        self, client, project
    ):
        client.connection.get.side_effect = [
            response(
                table(
                    [
                        {**labeler("user-1"), "memberType": "internal"},
                        {**labeler("user-2"), "memberType": "external"},
                    ],
                    total=2,
                )
            ),
            response(table([{**REVIEWER, "memberType": "external"}], total=1)),
        ]

        labelers = list(
            Project.get_labeler_performance(project, "2026-01-01", "2026-01-07")
        )
        reviewers = list(
            Project.get_reviewer_performance(
                project, "2026-01-01", "2026-01-07"
            )
        )

        assert [row.member_type for row in labelers] == [
            "internal",
            "external",
        ]
        assert reviewers[0].member_type == PerformanceMemberType.EXTERNAL

    def test_reads_a_reply_from_an_api_that_does_not_say(self, client, project):
        client.connection.get.return_value = response(
            table([labeler("user-1")], total=1)
        )

        (row,) = Project.get_labeler_performance(
            project, "2026-01-01", "2026-01-07"
        )

        assert row.member_type is None


class TestRetries:
    def test_tries_again_after_a_failure_of_the_service(self, client, project):
        client.connection.get.side_effect = [
            response({"statusCode": 503, "message": "Unavailable"}, 503),
            response({"statusCode": 500, "message": "Oops"}, 500),
            response(SERIES),
        ]

        series = Project.get_performance_metric(
            project, "labels_created", "2026-01-01", "2026-01-07"
        )

        assert series.metric == "labels_created"
        assert client.connection.get.call_count == 3

    def test_tries_again_after_a_timeout(self, client, project):
        client.connection.get.side_effect = [
            requests.exceptions.ReadTimeout("read timed out"),
            response(SERIES),
        ]

        Project.get_performance_metric(
            project, "labels_created", "2026-01-01", "2026-01-07"
        )

        assert client.connection.get.call_count == 2

    def test_tries_a_failed_page_again_without_repeating_rows(
        self, client, project
    ):
        client.connection.get.side_effect = [
            response(table([labeler("user-1")], total=2)),
            response({"statusCode": 502, "message": "Bad gateway"}, 502),
            response(table([labeler("user-2")], total=2, page=2)),
        ]

        rows = list(
            Project.get_labeler_performance(
                project, "2026-01-01", "2026-01-07", page_size=1
            )
        )

        assert [row.user_id for row in rows] == ["user-1", "user-2"]
        assert [sent(client, call)[1]["page"] for call in (0, 1, 2)] == [
            "1",
            "2",
            "2",
        ]

    @pytest.mark.parametrize("status", [400, 401, 403, 404, 429])
    def test_does_not_repeat_a_request_that_was_refused(
        self, client, project, status
    ):
        client.connection.get.return_value = response(
            {"statusCode": status, "message": "No"}, status
        )

        with pytest.raises(LabelboxError):
            Project.get_performance_metric(
                project, "labels_created", "2026-01-01", "2026-01-07"
            )

        assert client.connection.get.call_count == 1

    def test_reports_the_failure_itself_once_it_stops_trying(
        self, client, project
    ):
        client.connection.get.return_value = response(
            {"statusCode": 503, "message": "Under maintenance"}, 503
        )

        with pytest.raises(InternalServerError, match="Under maintenance"):
            Project.get_performance_metric(
                project, "labels_created", "2026-01-01", "2026-01-07"
            )

        assert client.connection.get.call_count > 1

    def test_has_time_left_to_try_again_after_a_request_that_timed_out(
        self,
    ):
        # A retry starts only if the deadline, counted from the first attempt,
        # has not passed after the failed attempt and the pause that follows.
        one_attempt = performance._TIMEOUT_SECONDS
        longest_first_pause = 2  # seconds, across google-api-core versions

        assert SHIPPED_RETRY.deadline >= one_attempt + longest_first_pause
        # ...and it does not start a third attempt after two timeouts.
        assert SHIPPED_RETRY.deadline <= 2 * one_attempt

    def test_reports_a_timeout_as_the_sdk_does(self, client, project):
        client.connection.get.side_effect = requests.exceptions.ReadTimeout(
            "read timed out"
        )

        with pytest.raises(TimeoutError, match="read timed out"):
            Project.get_performance_metric(
                project, "labels_created", "2026-01-01", "2026-01-07"
            )

    def test_reports_a_connection_failure_without_repeating_it(
        self, client, project
    ):
        client.connection.get.side_effect = requests.exceptions.ConnectionError(
            "connection refused"
        )

        with pytest.raises(NetworkError):
            Project.get_performance_metric(
                project, "labels_created", "2026-01-01", "2026-01-07"
            )

        assert client.connection.get.call_count == 1


class TestErrors:
    @pytest.mark.parametrize(
        "status, error",
        [
            (400, InvalidQueryError),
            (401, AuthenticationError),
            (403, AuthorizationError),
            (404, ResourceNotFoundError),
            (429, ApiLimitError),
            (500, InternalServerError),
            (503, InternalServerError),
            (418, LabelboxError),
        ],
    )
    def test_raises_the_sdk_error_for_the_status(
        self, client, project, status, error
    ):
        client.connection.get.return_value = response(
            {"statusCode": status, "message": "Something went wrong"}, status
        )

        with pytest.raises(error, match="Something went wrong"):
            Project.get_performance_metric(
                project, "labels_created", "2026-01-01", "2026-01-07"
            )

    def test_names_the_parameters_the_api_refused(self, client, project):
        client.connection.get.return_value = response(
            {
                "statusCode": 400,
                "error": "Bad Request",
                "message": "Invalid query parameters",
                "details": [
                    {
                        "parameter": "endDate",
                        "message": "must not be before startDate",
                    },
                    {
                        "parameter": "interval",
                        "message": "must be one of day, week, month, quarter, year",
                    },
                ],
            },
            400,
        )

        with pytest.raises(InvalidQueryError) as raised:
            Project.get_performance_metric(
                project,
                "labels_created",
                "2026-01-07",
                "2026-01-01",
                interval="hour",
            )

        message = str(raised.value)
        assert "endDate must not be before startDate" in message
        assert "interval must be one of day, week" in message

    def test_says_which_project_was_not_found(self, client, project):
        client.connection.get.return_value = response(
            {
                "statusCode": 404,
                "message": "Project project-1 was not found.",
                "error": "Not Found",
            },
            404,
        )

        with pytest.raises(
            ResourceNotFoundError, match="Project project-1 was not found"
        ):
            list(
                Project.get_labeler_performance(
                    project, "2026-01-01", "2026-01-07"
                )
            )

    def test_reports_a_reply_that_is_not_json(self, client, project):
        reply = Mock()
        reply.status_code = 502
        reply.json.side_effect = ValueError("not json")
        reply.text = "Bad gateway"
        client.connection.get.return_value = reply

        with pytest.raises(InternalServerError, match="Bad gateway"):
            Project.get_performance_metric(
                project, "labels_created", "2026-01-01", "2026-01-07"
            )
