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
    PerformanceCursorRows,
    PerformanceDeletedLabels,
    PerformanceInterval,
    PerformanceMemberType,
    PerformanceScoreBucket,
    PerformanceTableChangedError,
    PerformanceTimeBucket,
    Project,
    SignInEndReason,
    SignInEventRows,
    SignInEventType,
    SignInSessionStatus,
    SignInStartKind,
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

    def test_leaves_a_filter_out_when_it_is_not_given(self, client, project):
        Project.get_performance_metric(
            project,
            "labels_created",
            "2026-01-01",
            "2026-01-07",
            user_ids=None,
        )

        _, params = sent(client)
        assert "userIds" not in params

    @pytest.mark.parametrize(
        "argument",
        ["user_ids", "user_group_ids", "batch_ids"],
    )
    @pytest.mark.parametrize("empty", [[], (), set(), iter([])])
    def test_refuses_an_empty_filter_instead_of_reporting_on_everyone(
        self, client, project, argument, empty
    ):
        with pytest.raises(ValueError, match=f"{argument} is empty"):
            Project.get_performance_metric(
                project,
                "labels_created",
                "2026-01-01",
                "2026-01-07",
                **{argument: empty},
            )

        client.connection.get.assert_not_called()

    @pytest.mark.parametrize(
        "argument",
        [
            "project_ids",
            "owner_organization_ids",
            "user_ids",
            "member_organization_ids",
            "user_group_ids",
        ],
    )
    def test_refuses_an_empty_workspace_filter_too(self, client, argument):
        with pytest.raises(ValueError, match=f"{argument} is empty"):
            client.get_workspace_performance_metric(
                "labels_created", "2026-01-01", "2026-01-07", **{argument: []}
            )
        with pytest.raises(ValueError, match=f"{argument} is empty"):
            client.get_workspace_labeler_performance(
                "2026-01-01", "2026-01-07", **{argument: []}
            )

        client.connection.get.assert_not_called()

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

    def test_says_when_the_table_changed_between_pages(self, client, project):
        # A member joined while the table was read: user-1 moves to page 2.
        client.connection.get.side_effect = [
            response(table([labeler("user-1"), labeler("user-2")], total=4)),
            response(
                table([labeler("user-1"), labeler("user-2")], total=5, page=2)
            ),
        ]

        rows = Project.get_labeler_performance(
            project, "2026-01-01", "2026-01-07", page_size=2
        )
        read = []
        with pytest.raises(
            PerformanceTableChangedError,
            match="page 1 counted 4 rows and page 2 counts 5",
        ):
            for row in rows:
                read.append(row.user_id)

        # The first page was returned before the change could be seen.
        assert read == ["user-1", "user-2"]
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

    @pytest.mark.parametrize(
        "sort_by, sent_as",
        [
            ("labels_created", "labelsCreated"),
            ("avg_time_per_label", "avgTimePerLabel"),
            ("rework_percentage", "reworkPercentage"),
            # Already in the API's spelling: passed on as it is.
            ("labelsCreated", "labelsCreated"),
            ("avgTimePerLabel", "avgTimePerLabel"),
        ],
    )
    def test_spells_the_sort_column_as_the_api_does(
        self, client, project, sort_by, sent_as
    ):
        client.connection.get.return_value = response(table([], total=0))

        list(
            Project.get_labeler_performance(
                project, "2026-01-01", "2026-01-07", sort_by=sort_by
            )
        )

        assert sent(client)[1]["sort"] == sent_as

    def test_reads_the_table_again_on_a_second_pass(self, client, project):
        first = [
            response(table([labeler("user-1")], total=2)),
            response(table([labeler("user-2")], total=2, page=2)),
        ]
        # By the second pass a row has been added, in front of the others.
        second = [
            response(table([labeler("user-0")], total=3)),
            response(table([labeler("user-1")], total=3, page=2)),
            response(table([labeler("user-2")], total=3, page=3)),
        ]
        client.connection.get.side_effect = first + second

        rows = Project.get_labeler_performance(
            project, "2026-01-01", "2026-01-07", page_size=1
        )
        once = [row.user_id for row in rows]
        twice = [row.user_id for row in rows]

        assert once == ["user-1", "user-2"]
        # Not page 1 as it was, followed by pages 2 and 3 as they are now.
        assert twice == ["user-0", "user-1", "user-2"]
        assert rows.total == 3
        assert [sent(client, call)[1]["page"] for call in range(5)] == [
            "1",
            "2",
            "1",
            "2",
            "3",
        ]

    def test_reads_the_total_then_the_rows_with_one_request_for_the_first_page(
        self, client, project
    ):
        client.connection.get.return_value = response(
            table([labeler("user-1")], total=1)
        )

        rows = Project.get_labeler_performance(
            project, "2026-01-01", "2026-01-07"
        )
        assert rows.total == 1
        assert [row.user_id for row in rows] == ["user-1"]
        assert rows.total == 1

        assert client.connection.get.call_count == 1

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
                "skippedProjectIds": ["project-9"],
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
        assert series.skipped_project_ids == ["project-9"]

    def test_sends_no_narrowing_unless_asked(self, client):
        client.get_workspace_performance_metric(
            "labels_created", "2026-01-01", "2026-01-07"
        )
        client.connection.get.return_value = response(workspace_table([], 0))
        list(
            client.get_workspace_labeler_performance("2026-01-01", "2026-01-07")
        )

        for call in (0, 1):
            _, params = sent(client, call)
            assert "memberType" not in params
            assert "ownerOrganizationIds" not in params
            assert "memberOrganizationIds" not in params
            assert "userGroupIds" not in params

    def test_narrows_a_metric_by_user_group_and_member_organization(
        self, client
    ):
        client.connection.get.return_value = response(
            {
                **{k: v for k, v in SERIES.items() if k != "projectId"},
                "organizationId": "org-1",
                "projectIds": None,
                "ownerOrganizationIds": None,
                "memberOrganizationIds": ["org-2", "org-3"],
                "memberType": None,
                "userGroupIds": ["group-a", "GROUP-B"],
                "skippedProjectIds": [],
            }
        )

        series = client.get_workspace_performance_metric(
            "labels_created",
            "2026-01-01",
            "2026-01-07",
            member_organization_ids=["org-2", SimpleNamespace(uid="org-3")],
            # UserGroup is a pydantic model whose ID is `id`, not `uid`.
            user_group_ids=[
                UserGroup(client=client, id="group-a", name="Vendor A"),
                "GROUP-B",
            ],
        )

        _, params = sent(client)
        assert params["memberOrganizationIds"] == "org-2,org-3"
        assert params["userGroupIds"] == "group-a,GROUP-B"
        assert series.member_organization_ids == ["org-2", "org-3"]
        # Echoed as sent.
        assert series.user_group_ids == ["group-a", "GROUP-B"]

    def test_says_when_a_group_filtered_table_changed_between_pages(
        self, client
    ):
        # Group membership is worked out for every page; one member left.
        client.connection.get.side_effect = [
            response(
                workspace_table(
                    [
                        workspace_labeler("user-1", "project-1"),
                        workspace_labeler("user-2", "project-1"),
                    ],
                    total=3,
                )
            ),
            response(workspace_table([], total=2, page=2)),
        ]

        rows = client.get_workspace_labeler_performance(
            "2026-01-01", "2026-01-07", user_group_ids=["group-a"], page_size=2
        )

        with pytest.raises(PerformanceTableChangedError, match="Read it again"):
            list(rows)

    def test_reads_a_metric_from_an_api_that_does_not_echo_them(self, client):
        client.connection.get.return_value = response(
            {
                **{k: v for k, v in SERIES.items() if k != "projectId"},
                "organizationId": "org-1",
            }
        )

        series = client.get_workspace_performance_metric(
            "labels_created", "2026-01-01", "2026-01-07"
        )

        assert series.member_organization_ids is None
        assert series.user_group_ids is None

    def test_reports_too_many_group_members_as_an_invalid_query(self, client):
        client.connection.get.return_value = response(
            {
                "statusCode": 400,
                "error": "Bad Request",
                "message": "The selected user groups have 5200 members; a "
                "performance report can be filtered by at most 5000",
                "details": [
                    {
                        "parameter": "userGroupIds",
                        "message": "selects 5200 members; at most 5000 can "
                        "be reported on",
                    }
                ],
            },
            status=400,
        )

        with pytest.raises(InvalidQueryError, match="userGroupIds selects"):
            list(
                client.get_workspace_labeler_performance(
                    "2026-01-01", "2026-01-07", user_group_ids=["group-a"]
                )
            )

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

    def test_narrows_the_workspace_table_by_user_group_and_member_organization(
        self, client
    ):
        client.connection.get.return_value = response(
            workspace_table(
                [
                    workspace_labeler(
                        "user-1",
                        "project-1",
                        memberType="external",
                        memberOrganizationId="org-2",
                        memberOrganizationName="Vendor org",
                    )
                ],
                1,
            )
        )

        (row,) = client.get_workspace_labeler_performance(
            "2026-01-01",
            "2026-01-07",
            member_organization_ids=["org-2"],
            user_group_ids=[
                UserGroup(client=client, id="group-a", name="Vendor A")
            ],
        )

        _, params = sent(client)
        assert params["memberOrganizationIds"] == "org-2"
        assert params["userGroupIds"] == "group-a"
        assert row.member_organization_id == "org-2"
        assert row.member_organization_name == "Vendor org"

    def test_reads_a_row_whose_project_can_no_longer_be_found(self, client):
        client.connection.get.return_value = response(
            workspace_table(
                [
                    workspace_labeler(
                        "user-1",
                        "project-gone",
                        projectName=None,
                        projectOrganizationId=None,
                        projectOrganizationName=None,
                        isProjectDeleted=True,
                    )
                ],
                1,
            )
        )

        (row,) = client.get_workspace_labeler_performance(
            "2026-01-01", "2026-01-07"
        )

        assert row.project_id == "project-gone"
        assert row.project_name is None
        assert row.project_organization_id is None
        assert row.project_organization_name is None
        assert row.is_project_deleted is True
        assert row.labels_created == 12

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
        assert row.member_organization_id is None
        assert row.member_organization_name is None


class TestMemberOrganization:
    def test_says_whose_organization_each_member_belongs_to(
        self, client, project
    ):
        client.connection.get.side_effect = [
            response(
                table(
                    [
                        {
                            **labeler("user-1"),
                            "memberType": "internal",
                            "memberOrganizationId": "org-1",
                            "memberOrganizationName": "Org one",
                        },
                        {
                            **labeler("user-2"),
                            "memberType": "external",
                            "memberOrganizationId": "org-2",
                            # Masked for a caller who may not see it.
                            "memberOrganizationName": "org.name.org-2",
                        },
                    ],
                    total=2,
                )
            ),
            response(
                table(
                    [
                        {
                            **REVIEWER,
                            "memberType": "external",
                            "memberOrganizationId": "org-2",
                            "memberOrganizationName": "Vendor org",
                        }
                    ],
                    total=1,
                )
            ),
        ]

        labelers = list(
            Project.get_labeler_performance(project, "2026-01-01", "2026-01-07")
        )
        reviewers = list(
            Project.get_reviewer_performance(
                project, "2026-01-01", "2026-01-07"
            )
        )

        assert [
            (row.member_organization_id, row.member_organization_name)
            for row in labelers
        ] == [("org-1", "Org one"), ("org-2", "org.name.org-2")]
        assert reviewers[0].member_organization_id == "org-2"
        assert reviewers[0].member_organization_name == "Vendor org"

    def test_reads_a_member_whose_account_or_organization_is_gone(self, client):
        client.connection.get.return_value = response(
            workspace_table(
                [
                    workspace_labeler(
                        "user-gone",
                        "project-1",
                        memberType=None,
                        memberOrganizationId=None,
                        memberOrganizationName=None,
                    ),
                    workspace_labeler(
                        "user-2",
                        "project-1",
                        memberOrganizationId="org-gone",
                        memberOrganizationName=None,
                    ),
                ],
                2,
            )
        )

        gone, orphaned = client.get_workspace_labeler_performance(
            "2026-01-01", "2026-01-07"
        )

        assert gone.member_organization_id is None
        assert gone.member_organization_name is None
        assert orphaned.member_organization_id == "org-gone"
        assert orphaned.member_organization_name is None


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

    @pytest.mark.parametrize(
        "failure",
        [
            response({"statusCode": 500, "message": "Oops"}, 500),
            requests.exceptions.ReadTimeout("read timed out"),
        ],
    )
    def test_raises_an_error_whose_causes_do_not_lead_back_to_it(
        self, client, project, failure
    ):
        # A chain that loops makes some traceback printers run forever.
        if isinstance(failure, Exception):
            client.connection.get.side_effect = failure
        else:
            client.connection.get.return_value = failure

        with pytest.raises(LabelboxError) as raised:
            Project.get_performance_metric(
                project, "labels_created", "2026-01-01", "2026-01-07"
            )

        seen = []
        error = raised.value
        while error is not None:
            assert not any(error is earlier for earlier in seen)
            seen.append(error)
            error = error.__cause__ or error.__context__
        assert len(seen) < 5

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


RULES = {
    "cookieLifetimeSeconds": 302400,
    "signInTokenLifetimeSeconds": 86400,
    "workspaceTokenLifetimeSeconds": 604800,
}


def sign_in_session(session_id, **fields):
    """A session with a recorded end, as the REST API returns it."""
    return {
        "sessionId": session_id,
        "userId": "user-1",
        "email": "user-1@example.com",
        "memberDeleted": False,
        "startedAt": "2026-11-03T08:59:41.120Z",
        "startKind": "SIGN_IN",
        "status": "ENDED",
        "endedAt": "2026-11-03T17:31:02.507Z",
        "endReason": "SIGNED_OUT",
        "endDerived": False,
        "expiresAt": "2026-11-06T21:00:41.120Z",
        "durationSeconds": 30681,
        **fields,
    }


def sessions_page(rows, next_cursor=None):
    return {
        "organizationId": "org-1",
        "startDate": "2026-11-02",
        "endDate": "2026-11-08",
        "userIds": None,
        "userGroupIds": None,
        "status": None,
        "rules": RULES,
        "data": rows,
        "nextCursor": next_cursor,
        "perPage": 100,
        "generatedAt": "2026-11-09T10:00:00.000Z",
    }


def sign_in_event(session_id, kind="in", **fields):
    """A sign-in, or with kind "out" a recorded sign-out."""
    signing_in = kind == "in"
    return {
        "eventId": f"{session_id}.{kind}",
        "type": "SIGN_IN" if signing_in else "SIGN_OUT",
        "occurredAt": "2026-11-03T08:59:41.120Z"
        if signing_in
        else "2026-11-03T17:31:02.507Z",
        "sessionId": session_id,
        "userId": "user-1",
        "email": "user-1@example.com",
        "startKind": "SIGN_IN" if signing_in else None,
        "endReason": None if signing_in else "SIGNED_OUT",
        "endDerived": None if signing_in else False,
        "sessionStartedAt": "2026-11-03T08:59:41.120Z",
        **fields,
    }


def events_page(
    rows, next_cursor=None, complete_through="2026-11-04T00:00:00.000Z"
):
    return {
        "organizationId": "org-1",
        "startDate": "2026-11-03",
        "endDate": "2026-11-03",
        "userIds": None,
        "userGroupIds": None,
        "types": ["SIGN_IN", "SIGN_OUT"],
        "includeDerived": True,
        "rules": RULES,
        "data": rows,
        "nextCursor": next_cursor,
        "completeThrough": complete_through,
        "perPage": 100,
        "generatedAt": "2026-11-09T10:00:00.000Z",
    }


def cursors_sent(client):
    """The cursor each request sent, None for none."""
    return [
        sent(client, call)[1].get("cursor")
        for call in range(client.connection.get.call_count)
    ]


class TestSignInSessions:
    def test_asks_for_nothing_until_the_sessions_are_read(self, client):
        sessions = client.get_sign_in_sessions("2026-11-02", "2026-11-08")

        client.connection.get.assert_not_called()
        assert isinstance(sessions, PerformanceCursorRows)

    def test_returns_the_sessions_that_started_in_the_period(self, client):
        client.connection.get.return_value = response(
            sessions_page([sign_in_session("session-1")])
        )

        (session,) = client.get_sign_in_sessions(
            date(2026, 11, 2), "2026-11-08"
        )

        url, params = sent(client)
        assert url == f"{BASE}/workspace/sign-in-sessions"
        assert params == {
            "startDate": "2026-11-02",
            "endDate": "2026-11-08",
            "perPage": "100",
        }
        assert session.session_id == "session-1"
        assert session.user_id == "user-1"
        assert session.email == "user-1@example.com"
        assert session.member_deleted is False
        assert session.started_at == datetime(
            2026, 11, 3, 8, 59, 41, 120000, tzinfo=timezone.utc
        )
        assert session.start_kind == SignInStartKind.SIGN_IN
        assert session.status == SignInSessionStatus.ENDED
        assert session.ended_at == datetime(
            2026, 11, 3, 17, 31, 2, 507000, tzinfo=timezone.utc
        )
        assert session.end_reason == SignInEndReason.SIGNED_OUT
        assert session.end_derived is False
        assert session.expires_at == datetime(
            2026, 11, 6, 21, 0, 41, 120000, tzinfo=timezone.utc
        )
        assert session.duration_seconds == 30681

    def test_sends_the_filters_under_the_names_the_api_gives_them(self, client):
        client.connection.get.return_value = response(sessions_page([]))

        list(
            client.get_sign_in_sessions(
                "2026-11-02",
                "2026-11-08",
                user_ids=["user-1", SimpleNamespace(uid="user-2")],
                # UserGroup is a pydantic model whose ID is `id`, not `uid`.
                user_group_ids=[
                    UserGroup(client=client, id="group-a", name="Vendor A"),
                    "group-b",
                ],
                status=SignInSessionStatus.OPEN,
                page_size=25,
            )
        )

        _, params = sent(client)
        assert params == {
            "startDate": "2026-11-02",
            "endDate": "2026-11-08",
            "userIds": "user-1,user-2",
            "userGroupIds": "group-a,group-b",
            "status": "open",
            "perPage": "25",
        }

    @pytest.mark.parametrize(
        "status, sent_as",
        [
            (SignInSessionStatus.OPEN, "open"),
            (SignInSessionStatus.ENDED, "ended"),
            ("open", "open"),
            ("ended", "ended"),
            # As a session's own status spells it.
            ("OPEN", "open"),
            ("ENDED", "ended"),
        ],
    )
    def test_sends_the_status_in_lower_case_as_the_api_takes_it(
        self, client, status, sent_as
    ):
        client.connection.get.return_value = response(sessions_page([]))

        list(
            client.get_sign_in_sessions(
                "2026-11-02", "2026-11-08", status=status
            )
        )

        assert sent(client)[1]["status"] == sent_as

    def test_follows_the_cursor_until_there_is_no_next_page(self, client):
        client.connection.get.side_effect = [
            response(
                sessions_page(
                    [
                        sign_in_session("session-1"),
                        sign_in_session("session-2"),
                    ],
                    next_cursor="cursor-after-2",
                )
            ),
            response(
                sessions_page(
                    [
                        sign_in_session("session-3"),
                        sign_in_session("session-4"),
                    ],
                    next_cursor="cursor-after-4",
                )
            ),
            response(sessions_page([sign_in_session("session-5")])),
        ]

        sessions = list(
            client.get_sign_in_sessions(
                "2026-11-02", "2026-11-08", status="ended", page_size=2
            )
        )

        assert [session.session_id for session in sessions] == [
            "session-1",
            "session-2",
            "session-3",
            "session-4",
            "session-5",
        ]
        # Each page continues from the cursor the page before returned, as
        # it was returned, and asks for the same rows otherwise.
        assert cursors_sent(client) == [
            None,
            "cursor-after-2",
            "cursor-after-4",
        ]
        for call in range(3):
            _, params = sent(client, call)
            assert params["status"] == "ended"
            assert params["perPage"] == "2"
            assert params["startDate"] == "2026-11-02"

    def test_reads_an_empty_period_with_one_request(self, client):
        client.connection.get.return_value = response(sessions_page([]))

        assert (
            list(client.get_sign_in_sessions("2026-11-02", "2026-11-08")) == []
        )
        assert client.connection.get.call_count == 1

    def test_reads_the_sessions_again_from_the_first_page_on_a_second_pass(
        self, client
    ):
        first = [
            response(
                sessions_page(
                    [sign_in_session("session-1")], next_cursor="cursor-1"
                )
            ),
            response(sessions_page([sign_in_session("session-2")])),
        ]
        # By the second pass another session has started.
        second = [
            response(
                sessions_page(
                    [sign_in_session("session-1")], next_cursor="cursor-1"
                )
            ),
            response(
                sessions_page(
                    [sign_in_session("session-2")], next_cursor="cursor-2"
                )
            ),
            response(sessions_page([sign_in_session("session-3")])),
        ]
        client.connection.get.side_effect = first + second

        sessions = client.get_sign_in_sessions(
            "2026-11-02", "2026-11-08", page_size=1
        )
        once = [session.session_id for session in sessions]
        twice = [session.session_id for session in sessions]

        assert once == ["session-1", "session-2"]
        assert twice == ["session-1", "session-2", "session-3"]
        assert cursors_sent(client) == [
            None,
            "cursor-1",
            None,
            "cursor-1",
            "cursor-2",
        ]

    def test_reads_a_derived_end(self, client):
        client.connection.get.return_value = response(
            sessions_page(
                [
                    sign_in_session(
                        "session-1",
                        startedAt="2026-11-04T09:02:10.004Z",
                        endedAt="2026-11-07T21:03:10.004Z",
                        endReason="MAX_DURATION_REACHED",
                        endDerived=True,
                        expiresAt="2026-11-07T21:03:10.004Z",
                        durationSeconds=302460,
                    )
                ]
            )
        )

        (session,) = client.get_sign_in_sessions("2026-11-02", "2026-11-08")

        assert session.status == SignInSessionStatus.ENDED
        assert session.end_reason == SignInEndReason.MAX_DURATION_REACHED
        assert session.end_derived is True
        # The latest the session could last, not when the member left.
        assert session.ended_at == session.expires_at
        assert session.duration_seconds == 302460

    def test_reads_an_open_session(self, client):
        client.connection.get.return_value = response(
            sessions_page(
                [
                    sign_in_session(
                        "session-1",
                        startKind="WORKSPACE_SWITCH",
                        status="OPEN",
                        endedAt=None,
                        endReason=None,
                        endDerived=None,
                        durationSeconds=None,
                    )
                ]
            )
        )

        (session,) = client.get_sign_in_sessions(
            "2026-11-02", "2026-11-08", status="open"
        )

        assert session.status == SignInSessionStatus.OPEN
        assert session.start_kind == SignInStartKind.WORKSPACE_SWITCH
        assert session.ended_at is None
        assert session.end_reason is None
        assert session.end_derived is None
        assert session.duration_seconds is None
        assert session.expires_at == datetime(
            2026, 11, 6, 21, 0, 41, 120000, tzinfo=timezone.utc
        )

    def test_reads_a_member_whose_account_is_now_another_organizations(
        self, client
    ):
        client.connection.get.return_value = response(
            sessions_page(
                [sign_in_session("session-1", email=None, memberDeleted=True)]
            )
        )

        (session,) = client.get_sign_in_sessions("2026-11-02", "2026-11-08")

        assert session.email is None
        assert session.member_deleted is True
        assert session.user_id == "user-1"

    def test_ignores_fields_added_to_the_response_later(self, client):
        client.connection.get.return_value = response(
            {
                **sessions_page(
                    [sign_in_session("session-1", deviceKind="browser")]
                ),
                "asOf": "2026-11-09T10:00:00.000Z",
            }
        )

        (session,) = client.get_sign_in_sessions("2026-11-02", "2026-11-08")

        assert session.session_id == "session-1"
        assert not hasattr(session, "device_kind")

    def test_tries_a_failed_page_again_with_the_same_cursor(self, client):
        client.connection.get.side_effect = [
            response(
                sessions_page(
                    [sign_in_session("session-1")], next_cursor="cursor-1"
                )
            ),
            response({"statusCode": 502, "message": "Bad gateway"}, 502),
            response(sessions_page([sign_in_session("session-2")])),
        ]

        sessions = list(client.get_sign_in_sessions("2026-11-02", "2026-11-08"))

        assert [session.session_id for session in sessions] == [
            "session-1",
            "session-2",
        ]
        assert cursors_sent(client) == [None, "cursor-1", "cursor-1"]


class TestSignInEvents:
    def test_asks_for_nothing_until_the_events_are_read(self, client):
        events = client.get_sign_in_events("2026-11-03", "2026-11-03")

        client.connection.get.assert_not_called()
        assert isinstance(events, SignInEventRows)
        assert events.complete_through is None

    def test_returns_the_sign_ins_and_sign_outs(self, client):
        client.connection.get.return_value = response(
            events_page(
                [
                    sign_in_event("session-1", "in"),
                    sign_in_event("session-1", "out"),
                ]
            )
        )

        sign_in, sign_out = client.get_sign_in_events(
            "2026-11-03", "2026-11-03"
        )

        url, params = sent(client)
        assert url == f"{BASE}/workspace/sign-in-events"
        # Both types and the derived sign-outs are the API's default.
        assert params == {
            "startDate": "2026-11-03",
            "endDate": "2026-11-03",
            "perPage": "100",
        }
        assert sign_in.event_id == "session-1.in"
        assert sign_in.type == SignInEventType.SIGN_IN
        assert sign_in.occurred_at == datetime(
            2026, 11, 3, 8, 59, 41, 120000, tzinfo=timezone.utc
        )
        assert sign_in.session_id == "session-1"
        assert sign_in.user_id == "user-1"
        assert sign_in.email == "user-1@example.com"
        assert sign_in.start_kind == SignInStartKind.SIGN_IN
        assert sign_in.end_reason is None
        assert sign_in.end_derived is None
        assert sign_in.session_started_at == sign_in.occurred_at
        assert sign_out.event_id == "session-1.out"
        assert sign_out.type == SignInEventType.SIGN_OUT
        assert sign_out.start_kind is None
        assert sign_out.end_reason == SignInEndReason.SIGNED_OUT
        assert sign_out.end_derived is False
        assert sign_out.session_started_at == sign_in.occurred_at

    def test_sends_the_filters_under_the_names_the_api_gives_them(self, client):
        client.connection.get.return_value = response(events_page([]))

        list(
            client.get_sign_in_events(
                "2026-11-03",
                "2026-11-09",
                user_ids=["user-1"],
                user_group_ids=[
                    UserGroup(client=client, id="group-a", name="Vendor A")
                ],
                types=[SignInEventType.SIGN_OUT],
                include_derived=False,
                page_size=10,
            )
        )

        _, params = sent(client)
        assert params == {
            "startDate": "2026-11-03",
            "endDate": "2026-11-09",
            "userIds": "user-1",
            "userGroupIds": "group-a",
            "types": "SIGN_OUT",
            "includeDerived": "false",
            "perPage": "10",
        }

    @pytest.mark.parametrize(
        "types, sent_as",
        [
            ([SignInEventType.SIGN_IN], "SIGN_IN"),
            (["SIGN_OUT"], "SIGN_OUT"),
            (
                [SignInEventType.SIGN_IN, "SIGN_OUT"],
                "SIGN_IN,SIGN_OUT",
            ),
            # One type on its own, as the ID filters take one ID.
            (SignInEventType.SIGN_OUT, "SIGN_OUT"),
            ("SIGN_IN", "SIGN_IN"),
        ],
    )
    def test_takes_the_types_as_enums_or_strings(self, client, types, sent_as):
        client.connection.get.return_value = response(events_page([]))

        list(client.get_sign_in_events("2026-11-03", "2026-11-03", types=types))

        assert sent(client)[1]["types"] == sent_as

    def test_sends_include_derived_only_to_leave_them_out(self, client):
        client.connection.get.return_value = response(events_page([]))

        list(
            client.get_sign_in_events(
                "2026-11-03", "2026-11-03", include_derived=True
            )
        )

        assert "includeDerived" not in sent(client)[1]

    @pytest.mark.parametrize("empty", [[], (), iter([])])
    def test_refuses_empty_types_before_asking(self, client, empty):
        with pytest.raises(ValueError, match="types is empty"):
            client.get_sign_in_events("2026-11-03", "2026-11-03", types=empty)

        client.connection.get.assert_not_called()

    def test_follows_the_cursor_and_says_where_the_last_page_stops(
        self, client
    ):
        client.connection.get.side_effect = [
            response(
                events_page(
                    [sign_in_event("session-1", "in")],
                    next_cursor="cursor-1",
                    complete_through="2026-11-09T09:54:00.000Z",
                )
            ),
            response(
                events_page(
                    [sign_in_event("session-1", "out")],
                    next_cursor="cursor-2",
                    complete_through="2026-11-09T09:54:30.000Z",
                )
            ),
            # Each page is read a little later, so stops a little later.
            response(
                events_page(
                    [sign_in_event("session-2", "in")],
                    complete_through="2026-11-09T09:55:00.000Z",
                )
            ),
        ]

        events = client.get_sign_in_events(
            "2026-11-03", "2026-11-09", page_size=1
        )
        read = []
        for event in events:
            # Not until the last page has been read.
            assert events.complete_through is None
            read.append(event.event_id)

        assert read == ["session-1.in", "session-1.out", "session-2.in"]
        assert cursors_sent(client) == [None, "cursor-1", "cursor-2"]
        assert events.complete_through == datetime(
            2026, 11, 9, 9, 55, tzinfo=timezone.utc
        )

    def test_says_nothing_of_where_the_feed_stops_if_it_was_not_read_to_the_end(
        self, client
    ):
        client.connection.get.return_value = response(
            events_page(
                [sign_in_event("session-1", "in")], next_cursor="cursor-1"
            )
        )

        events = client.get_sign_in_events("2026-11-03", "2026-11-03")
        next(iter(events))

        assert events.complete_through is None
        assert client.connection.get.call_count == 1

    def test_reads_the_feed_again_from_the_first_page_on_a_second_pass(
        self, client
    ):
        client.connection.get.side_effect = [
            response(
                events_page(
                    [sign_in_event("session-1", "in")],
                    next_cursor="cursor-1",
                    complete_through="2026-11-09T09:55:00.000Z",
                )
            ),
            response(
                events_page(
                    [sign_in_event("session-1", "out")],
                    complete_through="2026-11-09T09:55:00.000Z",
                )
            ),
            # By the second pass the feed has moved on by an event.
            response(
                events_page(
                    [
                        sign_in_event("session-1", "in"),
                        sign_in_event("session-1", "out"),
                        sign_in_event("session-2", "in"),
                    ],
                    complete_through="2026-11-09T10:05:00.000Z",
                )
            ),
        ]

        events = client.get_sign_in_events("2026-11-03", "2026-11-09")
        once = [event.event_id for event in events]
        first_stop = events.complete_through
        twice = []
        for event in events:
            # The first reading's stop does not describe this one.
            assert events.complete_through is None
            twice.append(event.event_id)

        assert once == ["session-1.in", "session-1.out"]
        assert twice == ["session-1.in", "session-1.out", "session-2.in"]
        assert cursors_sent(client) == [None, "cursor-1", None]
        assert first_stop == datetime(2026, 11, 9, 9, 55, tzinfo=timezone.utc)
        assert events.complete_through == datetime(
            2026, 11, 9, 10, 5, tzinfo=timezone.utc
        )

    def test_reads_a_derived_sign_out(self, client):
        client.connection.get.return_value = response(
            events_page(
                [
                    sign_in_event(
                        "session-1",
                        "out",
                        occurredAt="2026-11-07T21:03:10.004Z",
                        endReason="MAX_DURATION_REACHED",
                        endDerived=True,
                        sessionStartedAt="2026-11-04T09:02:10.004Z",
                    )
                ]
            )
        )

        (sign_out,) = client.get_sign_in_events("2026-11-07", "2026-11-07")

        assert sign_out.type == SignInEventType.SIGN_OUT
        assert sign_out.end_reason == SignInEndReason.MAX_DURATION_REACHED
        assert sign_out.end_derived is True
        assert sign_out.start_kind is None
        # The session started before the period and signs out in it.
        assert sign_out.session_started_at == datetime(
            2026, 11, 4, 9, 2, 10, 4000, tzinfo=timezone.utc
        )

    def test_reads_a_member_whose_account_is_now_another_organizations(
        self, client
    ):
        client.connection.get.return_value = response(
            events_page([sign_in_event("session-1", "in", email=None)])
        )

        (event,) = client.get_sign_in_events("2026-11-03", "2026-11-03")

        assert event.email is None
        assert event.user_id == "user-1"

    def test_ignores_fields_added_to_the_response_later(self, client):
        client.connection.get.return_value = response(
            {
                **events_page(
                    [sign_in_event("session-1", "in", deviceKind="browser")]
                ),
                "asOf": "2026-11-09T10:00:00.000Z",
            }
        )

        events = client.get_sign_in_events("2026-11-03", "2026-11-03")
        (event,) = events

        assert event.event_id == "session-1.in"
        assert not hasattr(event, "device_kind")
        assert events.complete_through == datetime(
            2026, 11, 4, tzinfo=timezone.utc
        )


class TestSignInFilters:
    @pytest.mark.parametrize("argument", ["user_ids", "user_group_ids"])
    @pytest.mark.parametrize("empty", [[], (), set(), iter([])])
    def test_refuses_an_empty_filter_instead_of_listing_everyone(
        self, client, argument, empty
    ):
        with pytest.raises(ValueError, match=f"{argument} is empty"):
            client.get_sign_in_sessions(
                "2026-11-02", "2026-11-08", **{argument: empty}
            )
        with pytest.raises(ValueError, match=f"{argument} is empty"):
            client.get_sign_in_events(
                "2026-11-02", "2026-11-08", **{argument: []}
            )

        client.connection.get.assert_not_called()

    @pytest.mark.parametrize(
        "day, expected",
        [
            (date(2026, 11, 2), "2026-11-02"),
            # The day an hour before a completeThrough, read as a UTC day.
            (
                datetime(2026, 11, 3, 0, 30, tzinfo=timezone.utc)
                - timedelta(hours=1),
                "2026-11-02",
            ),
            (
                datetime(
                    2026, 11, 2, 20, 0, tzinfo=timezone(timedelta(hours=-8))
                ),
                "2026-11-03",
            ),
            # A naive datetime is taken to be in UTC already: its own date.
            (datetime(2026, 11, 2, 20, 0), "2026-11-02"),
        ],
    )
    def test_sends_a_date_as_a_utc_day(self, client, day, expected):
        client.connection.get.side_effect = [
            response(sessions_page([])),
            response(events_page([])),
        ]

        list(client.get_sign_in_sessions(day, day))
        list(client.get_sign_in_events(day, day))

        for call in (0, 1):
            _, params = sent(client, call)
            assert params["startDate"] == expected
            assert params["endDate"] == expected

    @pytest.mark.parametrize(
        "status, error",
        [
            (400, InvalidQueryError),
            (401, AuthenticationError),
            (403, AuthorizationError),
            (429, ApiLimitError),
            (500, InternalServerError),
        ],
    )
    def test_raises_the_sdk_error_for_the_status(self, client, status, error):
        client.connection.get.return_value = response(
            {"statusCode": status, "message": "Something went wrong"}, status
        )

        with pytest.raises(error, match="Something went wrong"):
            list(client.get_sign_in_sessions("2026-11-02", "2026-11-08"))
        with pytest.raises(error, match="Something went wrong"):
            list(client.get_sign_in_events("2026-11-02", "2026-11-08"))

    def test_says_when_the_api_key_may_not_read_sign_ins(self, client):
        client.connection.get.return_value = response(
            {
                "statusCode": 403,
                "message": "This API key does not include the permission "
                "to view all performance.",
                "error": "Forbidden",
            },
            403,
        )

        with pytest.raises(
            AuthorizationError, match="permission to view all performance"
        ):
            list(client.get_sign_in_events("2026-11-02", "2026-11-08"))
        # A refusal is not tried again.
        assert client.connection.get.call_count == 1

    def test_names_the_parameters_the_api_refused(self, client):
        client.connection.get.return_value = response(
            {
                "statusCode": 400,
                "error": "Bad Request",
                "message": "Invalid query parameters",
                "details": [
                    {
                        "parameter": "endDate",
                        "message": "must be within 31 days of startDate",
                    },
                    {
                        "parameter": "types",
                        "message": "must be one or both of SIGN_IN, SIGN_OUT",
                    },
                ],
            },
            400,
        )

        with pytest.raises(InvalidQueryError) as raised:
            list(
                client.get_sign_in_events(
                    "2026-10-01", "2026-11-30", types=["sign_in"]
                )
            )

        message = str(raised.value)
        assert "endDate must be within 31 days of startDate" in message
        assert "types must be one or both of SIGN_IN, SIGN_OUT" in message
