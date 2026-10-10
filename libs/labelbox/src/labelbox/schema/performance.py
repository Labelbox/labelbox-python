"""Performance reports.

The numbers behind a project's Performance page and the workspace Monitor,
read through the Labelbox REST API (``/api/v1/performance``). The methods on
:class:`labelbox.Client` and :class:`labelbox.schema.project.Project` that
return the classes below are thin wrappers over the functions at the bottom
of this module.
"""

from datetime import date, datetime, timezone
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    Iterator,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
)
from urllib.parse import quote

import requests
from google.api_core import exceptions as core_exceptions
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

from labelbox.utils import _CamelCaseMixin

if TYPE_CHECKING:
    from labelbox import Client

# Reports are computed on request and a wide date range can take a while.
_TIMEOUT_SECONDS = 120
# How long a request is retried for, counted from its first attempt. Twice the
# time one attempt may take: enough to try once more after an attempt that
# timed out, and not to start a third.
_RETRY_DEADLINE_SECONDS = 2 * _TIMEOUT_SECONDS
_DEFAULT_PAGE_SIZE = 50

DateLike = Union[date, datetime, str]
"""A calendar day: a ``date``, a ``datetime`` or a string such as ``"2026-01-31"``."""


class PerformanceInterval(str, Enum):
    """The width of each bucket of a metric. Buckets follow UTC days."""

    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class PerformanceDeletedLabels(str, Enum):
    """Whether a report counts labels that were later deleted."""

    INCLUDE = "include"
    EXCLUDE = "exclude"
    ONLY = "only"


class PerformanceMemberType(str, Enum):
    """Whose account a member's is, seen from your organization.

    A project can be shared with another organization, such as a workforce
    provider, whose members then work in it. ``EXTERNAL`` is a member whose
    account belongs to another organization, or an Alignerr account; the
    Monitor calls these "Workforce members". ``INTERNAL`` is a member of your
    own organization.
    """

    INTERNAL = "internal"
    EXTERNAL = "external"


class PerformanceMetric(_CamelCaseMixin):
    """A metric that can be queried.

    Attributes:
        name (str): The name to pass to the metric methods, for example
            ``"labels_created"``.
        category (str): ``"throughput"``, ``"efficiency"`` or ``"quality"``.
        unit (str): ``"count"``, ``"seconds"`` or ``"percentage"``. A
            percentage is a fraction from 0 to 1: 0.9 means 90%.
        buckets (str): ``"time"`` for one value per interval, ``"score"`` for
            a histogram of agreement scores.
        description (str): What the metric measures, as the Performance page
            explains it.
    """

    name: str
    category: str
    unit: str
    buckets: str
    description: str


class PerformanceHandlingTime(_CamelCaseMixin):
    """Handling time split by activity, in seconds."""

    creating: float
    reviewing: float
    reworking: float


class PerformanceTimeBucket(_CamelCaseMixin):
    """The value of a metric over one interval.

    Attributes:
        start (datetime): Start of the interval, inclusive.
        end (datetime): End of the interval, exclusive.
        value (float): The metric's value, in the unit of its series.
        numerator (Optional[float]): For ratios, the amount divided.
        denominator (Optional[float]): For ratios, what it was divided by.
        modes (Optional[PerformanceHandlingTime]): The split by activity.
            Only average handling time metrics have it.
    """

    start: datetime
    end: datetime
    value: float
    numerator: Optional[float] = None
    denominator: Optional[float] = None
    modes: Optional[PerformanceHandlingTime] = None


class PerformanceScoreBucket(_CamelCaseMixin):
    """The number of labels whose agreement score falls in one range.

    Attributes:
        range_start (float): Lower bound of the range, inclusive.
        range_end (float): Upper bound of the range, exclusive.
        value (float): How many labels scored in the range.
    """

    range_start: float
    range_end: float
    value: float


class PerformanceMetricSeries(_CamelCaseMixin):
    """One metric over a period.

    Attributes:
        metric (str): The metric's name.
        unit (str): ``"count"``, ``"seconds"`` or ``"percentage"``. A
            percentage is a fraction from 0 to 1: 0.9 means 90%.
        bucket_type (str): ``"time"`` or ``"score"``; says which of the two
            bucket classes ``buckets`` holds.
        buckets (List[Union[PerformanceTimeBucket, PerformanceScoreBucket]]):
            The values.
        interval (str): The bucket width that was asked for.
        start_date (date): First day of the period.
        end_date (date): Last day of the period.
        generated_at (datetime): When the response was produced. This is not
            how fresh the underlying data is.
        project_id (Optional[str]): Set on a project's series.
        organization_id (Optional[str]): Set on a workspace series.
        project_ids (Optional[List[str]]): The projects a workspace series
            was narrowed to, if any.
        owner_organization_ids (Optional[List[str]]): The owning
            organizations a workspace series was narrowed to, if any.
        member_type (Optional[str]): The member type a workspace series was
            narrowed to, if any: ``"internal"`` or ``"external"``.
    """

    metric: str
    unit: str
    bucket_type: str
    buckets: List[Union[PerformanceTimeBucket, PerformanceScoreBucket]]
    interval: str
    start_date: date
    end_date: date
    generated_at: datetime
    project_id: Optional[str] = None
    organization_id: Optional[str] = None
    project_ids: Optional[List[str]] = None
    owner_organization_ids: Optional[List[str]] = None
    member_type: Optional[str] = None


class ProjectLabelerPerformance(_CamelCaseMixin):
    """One labeler's totals on a project over a period.

    Times are in seconds. Percentages and agreement scores are fractions from
    0 to 1: 0.9 means 90%. ``email`` is masked for labelers the caller may not
    identify, exactly as on the Performance page.

    Attributes:
        user_id (str)
        project_id (str)
        email (str)
        member_type (Optional[str]): ``"internal"`` for a member of your
            organization, ``"external"`` for a member of another one (see
            :class:`PerformanceMemberType`). ``None`` if the account no
            longer exists.
        labels_created (int)
        labels_skipped (int)
        member_total_time (float)
        labeling_time_submitted (float)
        labeling_time_skipped (float)
        reviews_received (int)
        review_time_all (float)
        rework_time_all (float)
        avg_time_per_label (float)
        avg_review_time_all (float)
        avg_rework_time_all (float)
        avg_benchmark_agreement (float)
        avg_consensus_agreement (float)
        rework_percentage (float)
        approval_percentage (float)
        avg_rating (Optional[float]): ``None`` when the labeler has no ratings.
        is_removed (bool): True when the labeler is no longer on the project.
    """

    user_id: str
    project_id: str
    email: str
    member_type: Optional[str] = None
    labels_created: int
    labels_skipped: int
    member_total_time: float
    labeling_time_submitted: float
    labeling_time_skipped: float
    reviews_received: int
    review_time_all: float
    rework_time_all: float
    avg_time_per_label: float
    avg_review_time_all: float
    avg_rework_time_all: float
    avg_benchmark_agreement: float
    avg_consensus_agreement: float
    rework_percentage: float
    approval_percentage: float
    avg_rating: Optional[float] = None
    is_removed: bool = False


class ProjectReviewerPerformance(_CamelCaseMixin):
    """One reviewer's totals on a project over a period.

    Times are in seconds. Percentages are fractions from 0 to 1: 0.9 means
    90%. ``email`` is masked for reviewers the caller may not identify,
    exactly as on the Performance page.

    Attributes:
        user_id (str)
        project_id (str)
        email (str)
        member_type (Optional[str]): ``"internal"`` for a member of your
            organization, ``"external"`` for a member of another one (see
            :class:`PerformanceMemberType`). ``None`` if the account no
            longer exists.
        labels_reviewed (int)
        labels_reworked (int)
        member_total_time (float)
        avg_review_time (float)
        avg_rework_time (float)
        review_time (float)
        rework_time (float)
        rework_percentage (float)
        approval_percentage (float)
        is_removed (bool): True when the reviewer is no longer on the project.
    """

    user_id: str
    project_id: str
    email: str
    member_type: Optional[str] = None
    labels_reviewed: int
    labels_reworked: int
    member_total_time: float
    avg_review_time: float
    avg_rework_time: float
    review_time: float
    rework_time: float
    rework_percentage: float
    approval_percentage: float
    is_removed: bool = False


class WorkspaceLabelerPerformance(_CamelCaseMixin):
    """One labeler's totals on one project, from the workspace report.

    A labeler who worked on several projects has one of these per project.
    Times are in seconds. Percentages and agreement scores are fractions from
    0 to 1: 0.9 means 90%. ``email`` is masked as on the Monitor.

    The report covers the projects your organization owns and the ones other
    organizations share with it. ``project_organization_id`` says which is
    which, and ``member_type`` whether the labeler is one of your own members.

    Attributes:
        user_id (str)
        email (str)
        member_type (Optional[str]): ``"internal"`` for a member of your
            organization, ``"external"`` for a member of another one (see
            :class:`PerformanceMemberType`). ``None`` if the account no
            longer exists.
        project_id (str)
        project_name (str)
        project_organization_id (str): The organization that owns the
            project. It differs from yours for a project shared with you.
        project_organization_name (str)
        is_project_deleted (bool)
        labels_created (int)
        labels_skipped (int)
        member_total_time (float)
        labeling_time_submitted (float)
        labeling_time_skipped (float)
        reviews_received (int)
        review_time_all (float)
        rework_time_all (float)
        avg_time_per_label (float)
        avg_review_time_all (float)
        avg_rework_time_all (float)
        avg_benchmark_agreement (float)
        avg_consensus_agreement (float)
        rework_percentage (float)
        approval_percentage (float)
        is_removed (bool)
    """

    user_id: str
    email: str
    member_type: Optional[str] = None
    project_id: str
    project_name: str
    project_organization_id: str
    project_organization_name: str
    is_project_deleted: bool
    labels_created: int
    labels_skipped: int
    member_total_time: float
    labeling_time_submitted: float
    labeling_time_skipped: float
    reviews_received: int
    review_time_all: float
    rework_time_all: float
    avg_time_per_label: float
    avg_review_time_all: float
    avg_rework_time_all: float
    avg_benchmark_agreement: float
    avg_consensus_agreement: float
    rework_percentage: float
    approval_percentage: float
    is_removed: bool = False


class PerformanceReportDownload(_CamelCaseMixin):
    """A link to a project's performance report as a file.

    Attributes:
        project_id (str)
        url (str): Where to download the file from. Anyone with the link can
            open it until it expires.
        expires_in_seconds (int): How long the link stays valid.
        start_date (date)
        end_date (date)
        generated_at (datetime)
    """

    project_id: str
    url: str
    expires_in_seconds: int
    start_date: date
    end_date: date
    generated_at: datetime


Row = TypeVar("Row", bound=_CamelCaseMixin)


class PerformanceRows(Generic[Row]):
    """The rows of a performance table.

    Iterating fetches the table a page at a time, so a large table is never
    held in one response. Nothing is requested until the rows, ``total`` or
    ``cached_at`` are read. The rows come in a fixed order, so no row is
    repeated or missed between pages.

    Iterating a second time reads the table again from its first page, and
    ``total`` and ``cached_at`` then describe that reading.

    >>> labelers = project.get_labeler_performance("2026-01-01", "2026-01-31")
    >>> labelers.total
    37
    >>> for labeler in labelers:
    ...     print(labeler.email, labeler.labels_created)
    """

    def __init__(
        self,
        fetch_page: Callable[[int], Dict[str, Any]],
        row_type: Type[Row],
    ):
        self._fetch_page = fetch_page
        self._row_type = row_type
        self._first_page: Optional[Dict[str, Any]] = None
        self._first_page_iterated = False

    def _page(self, number: int) -> Dict[str, Any]:
        if number != 1:
            return self._fetch_page(number)
        if self._first_page is None:
            self._first_page = self._fetch_page(1)
        return self._first_page

    @property
    def total(self) -> int:
        """The number of rows in the whole table."""
        return int(self._page(1)["total"])

    @property
    def cached_at(self) -> Optional[datetime]:
        """When the rows were computed, if they were served from a cache."""
        cached_at = self._page(1).get("cachedAt")
        return _parse_datetime(cached_at) if cached_at else None

    def __iter__(self) -> Iterator[Row]:
        if self._first_page_iterated:
            # The first page is kept so that reading ``total`` and then the
            # rows costs one request. A later pass must not start from that
            # old page and continue with new ones.
            self._first_page = None
        self._first_page_iterated = True

        number = 1
        seen = 0
        while True:
            page = self._page(number)
            rows = page["data"]
            for row in rows:
                yield self._row_type.model_validate(row)
            seen += len(rows)
            if not rows or seen >= int(page["total"]):
                return
            number += 1


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _to_day(value: DateLike) -> str:
    """The day as the API takes it. Reports follow UTC days."""
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            value = value.astimezone(timezone.utc)
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


def _to_id(value: Any) -> str:
    """The ID of a value that is an ID or an SDK object.

    Most SDK objects carry their ID as ``uid``; the pydantic ones, such as
    UserGroup, carry it as ``id``.
    """
    if isinstance(value, str):
        return value
    for attribute in ("uid", "id"):
        identifier = getattr(value, attribute, None)
        if isinstance(identifier, str) and identifier:
            return identifier
    raise TypeError(
        f"Expected an ID or an object that has one, got {type(value).__name__}"
    )


def _to_ids(name: str, values: Optional[Iterable[Any]]) -> Optional[str]:
    """IDs as one comma-separated parameter. Accepts IDs or SDK objects.

    ``None`` leaves the filter off. An empty list is refused: it is nearly
    always a list that came out empty, and leaving the filter off for it
    would report on everyone.
    """
    if values is None:
        return None
    if isinstance(values, str):
        values = [values]
    ids = [_to_id(value) for value in values]
    if not ids:
        raise ValueError(
            f"{name} is empty. Pass None to leave this filter off; "
            "an empty list would otherwise report on everyone."
        )
    return ",".join(ids)


def _to_field(attribute: str) -> str:
    """A row attribute as the API spells it: labels_created is labelsCreated.

    A name already in the API's spelling is left as it is.
    """
    head, *rest = attribute.split("_")
    return head + "".join(part[:1].upper() + part[1:] for part in rest)


def _to_query(params: Dict[str, Any]) -> Dict[str, str]:
    query: Dict[str, str] = {}
    for name, value in params.items():
        if value is None:
            continue
        if isinstance(value, bool):
            query[name] = "true" if value else "false"
        elif isinstance(value, Enum):
            query[name] = str(value.value)
        else:
            query[name] = str(value)
    return query


def _error_message(response: requests.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        body = None
    if not isinstance(body, dict):
        return response.text or f"HTTP {response.status_code}"

    message = body.get("message") or f"HTTP {response.status_code}"
    if isinstance(message, list):
        message = "; ".join(str(part) for part in message)
    details = body.get("details")
    if isinstance(details, list) and details:
        problems = "; ".join(
            f"{detail.get('parameter')} {detail.get('message')}"
            for detail in details
            if isinstance(detail, dict)
        )
        message = f"{message}: {problems}"
    return str(message)


def _raise_for_response(response: requests.Response) -> None:
    message = _error_message(response)
    status = response.status_code
    if status == 400:
        raise InvalidQueryError(message)
    if status == 401:
        raise AuthenticationError(message)
    if status == 403:
        raise AuthorizationError(message)
    if status == 404:
        raise ResourceNotFoundError(message=message)
    if status == 429:
        raise ApiLimitError(message)
    if status >= 500:
        raise InternalServerError(message)
    raise LabelboxError(message)


def _request(client: "Client", path: str, params: Dict[str, str]) -> Any:
    try:
        response = client.connection.get(
            f"{client.rest_endpoint}/performance{path}",
            params=params,
            timeout=_TIMEOUT_SECONDS,
        )
    except requests.exceptions.Timeout as error:
        raise TimeoutError(str(error))
    except requests.exceptions.RequestException as error:
        raise NetworkError(error)
    if response.status_code != requests.codes.ok:
        _raise_for_response(response)
    return response.json()


# Reading a report changes nothing, so a failure of the service or a timeout
# is tried again, with the growing pauses Client.execute retries a query with.
# The deadline is set here because the default (120 seconds) is already spent
# when a request of this length times out, and it would never be retried.
_retry_transient = retry.Retry(
    predicate=retry.if_exception_type(InternalServerError, TimeoutError),
    deadline=_RETRY_DEADLINE_SECONDS,
)


def _get(client: "Client", path: str, **params: Any) -> Dict[str, Any]:
    try:
        return _retry_transient(_request)(client, path, _to_query(params))
    except core_exceptions.RetryError as error:
        if not isinstance(error.cause, LabelboxError):
            raise
        failure = error.cause
    # Out of attempts: report what kept failing, not that retrying did. It is
    # raised out here, not inside the handler, because the retry error already
    # names the failure as its cause. Chaining the failure back to it would
    # make the two point at each other, and some traceback printers follow
    # such a chain forever.
    raise failure


def _segment(value: Any) -> str:
    """A value as one path segment, so an ID can never alter the path."""
    return quote(_to_id(value), safe="")


def _period(start_date: DateLike, end_date: DateLike) -> Dict[str, str]:
    return {"startDate": _to_day(start_date), "endDate": _to_day(end_date)}


def get_performance_metrics(client: "Client") -> List[PerformanceMetric]:
    body = _get(client, "/metrics")
    return [PerformanceMetric.model_validate(metric) for metric in body["data"]]


def get_project_metric(
    client: "Client",
    project_id: str,
    metric: str,
    start_date: DateLike,
    end_date: DateLike,
    interval: Union[PerformanceInterval, str],
    user_ids: Optional[Iterable[Any]],
    user_group_ids: Optional[Iterable[Any]],
    batch_ids: Optional[Iterable[Any]],
    deleted_labels: Union[PerformanceDeletedLabels, str],
) -> PerformanceMetricSeries:
    body = _get(
        client,
        f"/projects/{_segment(project_id)}/metrics/{_segment(metric)}",
        **_period(start_date, end_date),
        interval=interval,
        userIds=_to_ids("user_ids", user_ids),
        userGroupIds=_to_ids("user_group_ids", user_group_ids),
        batchIds=_to_ids("batch_ids", batch_ids),
        deletedLabels=deleted_labels,
    )
    return PerformanceMetricSeries.model_validate(body)


def _table(
    client: "Client",
    path: str,
    row_type: Type[Row],
    start_date: DateLike,
    end_date: DateLike,
    user_ids: Optional[Iterable[Any]],
    batch_ids: Optional[Iterable[Any]],
    deleted_labels: Union[PerformanceDeletedLabels, str],
    sort_by: Optional[str],
    descending: bool,
    page_size: int,
    **extra: Any,
) -> PerformanceRows[Row]:
    params = {
        **_period(start_date, end_date),
        "userIds": _to_ids("user_ids", user_ids),
        "batchIds": _to_ids("batch_ids", batch_ids),
        "deletedLabels": deleted_labels,
        # Columns are named as the row's attributes; the API spells them in
        # camel case.
        "sort": _to_field(sort_by) if sort_by else None,
        "order": ("desc" if descending else "asc") if sort_by else None,
        "perPage": page_size,
        **extra,
    }

    def fetch_page(number: int) -> Dict[str, Any]:
        return _get(client, path, page=number, **params)

    return PerformanceRows(fetch_page, row_type)


def get_project_labelers(
    client: "Client",
    project_id: str,
    start_date: DateLike,
    end_date: DateLike,
    user_ids: Optional[Iterable[Any]] = None,
    user_group_ids: Optional[Iterable[Any]] = None,
    batch_ids: Optional[Iterable[Any]] = None,
    deleted_labels: Union[
        PerformanceDeletedLabels, str
    ] = PerformanceDeletedLabels.INCLUDE,
    sort_by: Optional[str] = None,
    descending: bool = False,
    page_size: int = _DEFAULT_PAGE_SIZE,
    use_cache: bool = True,
) -> PerformanceRows[ProjectLabelerPerformance]:
    return _table(
        client,
        f"/projects/{_segment(project_id)}/labelers",
        ProjectLabelerPerformance,
        start_date,
        end_date,
        user_ids,
        batch_ids,
        deleted_labels,
        sort_by,
        descending,
        page_size,
        userGroupIds=_to_ids("user_group_ids", user_group_ids),
        # Only sent to skip the cache, which is on unless asked otherwise.
        useCache=None if use_cache else False,
    )


def get_project_reviewers(
    client: "Client",
    project_id: str,
    start_date: DateLike,
    end_date: DateLike,
    user_ids: Optional[Iterable[Any]] = None,
    user_group_ids: Optional[Iterable[Any]] = None,
    batch_ids: Optional[Iterable[Any]] = None,
    deleted_labels: Union[
        PerformanceDeletedLabels, str
    ] = PerformanceDeletedLabels.INCLUDE,
    sort_by: Optional[str] = None,
    descending: bool = False,
    page_size: int = _DEFAULT_PAGE_SIZE,
) -> PerformanceRows[ProjectReviewerPerformance]:
    return _table(
        client,
        f"/projects/{_segment(project_id)}/reviewers",
        ProjectReviewerPerformance,
        start_date,
        end_date,
        user_ids,
        batch_ids,
        deleted_labels,
        sort_by,
        descending,
        page_size,
        userGroupIds=_to_ids("user_group_ids", user_group_ids),
    )


def get_project_report_download(
    client: "Client",
    project_id: str,
    start_date: DateLike,
    end_date: DateLike,
    user_ids: Optional[Iterable[Any]] = None,
    user_group_ids: Optional[Iterable[Any]] = None,
    batch_ids: Optional[Iterable[Any]] = None,
    deleted_labels: Union[
        PerformanceDeletedLabels, str
    ] = PerformanceDeletedLabels.INCLUDE,
) -> PerformanceReportDownload:
    body = _get(
        client,
        f"/projects/{_segment(project_id)}/download",
        **_period(start_date, end_date),
        userIds=_to_ids("user_ids", user_ids),
        userGroupIds=_to_ids("user_group_ids", user_group_ids),
        batchIds=_to_ids("batch_ids", batch_ids),
        deletedLabels=deleted_labels,
    )
    return PerformanceReportDownload.model_validate(body)


def get_workspace_metric(
    client: "Client",
    metric: str,
    start_date: DateLike,
    end_date: DateLike,
    interval: Union[PerformanceInterval, str] = PerformanceInterval.DAY,
    project_ids: Optional[Iterable[Any]] = None,
    user_ids: Optional[Iterable[Any]] = None,
    batch_ids: Optional[Iterable[Any]] = None,
    deleted_labels: Union[
        PerformanceDeletedLabels, str
    ] = PerformanceDeletedLabels.INCLUDE,
    use_cache: bool = True,
    member_type: Optional[Union[PerformanceMemberType, str]] = None,
    owner_organization_ids: Optional[Iterable[Any]] = None,
) -> PerformanceMetricSeries:
    body = _get(
        client,
        f"/workspace/metrics/{_segment(metric)}",
        **_period(start_date, end_date),
        interval=interval,
        projectIds=_to_ids("project_ids", project_ids),
        userIds=_to_ids("user_ids", user_ids),
        batchIds=_to_ids("batch_ids", batch_ids),
        deletedLabels=deleted_labels,
        memberType=member_type,
        ownerOrganizationIds=_to_ids(
            "owner_organization_ids", owner_organization_ids
        ),
        useCache=None if use_cache else False,
    )
    return PerformanceMetricSeries.model_validate(body)


def get_workspace_labelers(
    client: "Client",
    start_date: DateLike,
    end_date: DateLike,
    project_ids: Optional[Iterable[Any]] = None,
    user_ids: Optional[Iterable[Any]] = None,
    batch_ids: Optional[Iterable[Any]] = None,
    deleted_labels: Union[
        PerformanceDeletedLabels, str
    ] = PerformanceDeletedLabels.INCLUDE,
    member_type: Optional[Union[PerformanceMemberType, str]] = None,
    owner_organization_ids: Optional[Iterable[Any]] = None,
    sort_by: Optional[str] = None,
    descending: bool = False,
    page_size: int = _DEFAULT_PAGE_SIZE,
    use_cache: bool = True,
) -> PerformanceRows[WorkspaceLabelerPerformance]:
    return _table(
        client,
        "/workspace/labelers",
        WorkspaceLabelerPerformance,
        start_date,
        end_date,
        user_ids,
        batch_ids,
        deleted_labels,
        sort_by,
        descending,
        page_size,
        projectIds=_to_ids("project_ids", project_ids),
        memberType=member_type,
        ownerOrganizationIds=_to_ids(
            "owner_organization_ids", owner_organization_ids
        ),
        useCache=None if use_cache else False,
    )
