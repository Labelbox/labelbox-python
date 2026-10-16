"""Performance reports.

The numbers behind a project's Performance page and the workspace Monitor,
and when the organization's members signed in and out, read through the
Labelbox REST API (``/api/v1/performance``). The methods on
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
# Sign-in activity is paged at most 100 rows at a time, and by default.
_SIGN_IN_PAGE_SIZE = 100

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

    An Alignerr account is external to everyone, Alignerr's own organization
    included.
    """

    INTERNAL = "internal"
    EXTERNAL = "external"


class SignInSessionStatus(str, Enum):
    """Whether a sign-in session is still open.

    A session is ``OPEN`` until it ends, by a recorded or a derived end, and
    ``ENDED`` after. Used as the ``status`` filter of
    :meth:`labelbox.Client.get_sign_in_sessions`, it is sent in lower case,
    as the API takes it there: ``open`` or ``ended``.
    """

    OPEN = "OPEN"
    ENDED = "ENDED"


class SignInStartKind(str, Enum):
    """How a sign-in session started.

    ``SIGN_IN``: the member signed in, by any method, including a single
    sign-on that completed without asking. ``WORKSPACE_SWITCH``: the member
    switched into this workspace from their user in another one.
    """

    SIGN_IN = "SIGN_IN"
    WORKSPACE_SWITCH = "WORKSPACE_SWITCH"


class SignInEndReason(str, Enum):
    """How a sign-in session ended.

    ``SIGNED_OUT``: the member signed out. This includes an idle sign-out by
    the label editor when the editor is shown inside another Labelbox page:
    the two cannot be told apart. ``REPLACED``: a new sign-in in the same
    browser replaced the session; it can be another account's, a sign-up or
    an impersonation. ``WORKSPACE_SWITCH``: the member switched
    to another workspace. ``ACCOUNT_REMOVED``: the member was removed from
    the organization or deactivated. ``REVOKED``: the session was ended
    because its account was merged into another.

    ``MAX_DURATION_REACHED``: nothing ended the session before every
    credential of its sign-in lapsed, at its ``expires_at``. This end is
    derived when the session is read, never recorded. It is when the session
    could last no longer, not when the member stopped working.

    Closing the tab or the browser is not recorded, and ends nothing. The
    label editor's idle sign-out when the editor is open in its own tab is
    not recorded either.
    """

    SIGNED_OUT = "SIGNED_OUT"
    REPLACED = "REPLACED"
    WORKSPACE_SWITCH = "WORKSPACE_SWITCH"
    ACCOUNT_REMOVED = "ACCOUNT_REMOVED"
    REVOKED = "REVOKED"
    MAX_DURATION_REACHED = "MAX_DURATION_REACHED"


class SignInEventType(str, Enum):
    """The kind of a sign-in event.

    ``SIGN_IN`` happens when a session starts, at its ``started_at``.
    ``SIGN_OUT`` happens when it ends, by a recorded or a derived end, at its
    ``ended_at``.
    """

    SIGN_IN = "SIGN_IN"
    SIGN_OUT = "SIGN_OUT"


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

    There are ten equal ranges, from 0 to 0.1 up to 0.9 to 1: fractions,
    like every score these reports return.

    Attributes:
        range_start (float): Lower bound of the range, from 0 to 0.9.
        range_end (float): Upper bound of the range, from 0.1 to 1.
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
        skipped_project_ids (Optional[List[str]]): On a workspace series
            narrowed by owning organization, the projects of those owners that
            are not counted because you may not view everyone's performance
            in them. Empty when none were left out.
        member_organization_ids (Optional[List[str]]): The member
            organizations a workspace series was narrowed to, if any.
        user_group_ids (Optional[List[str]]): The user groups a workspace
            series was narrowed to, if any, as they were sent.
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
    skipped_project_ids: Optional[List[str]] = None
    member_organization_ids: Optional[List[str]] = None
    user_group_ids: Optional[List[str]] = None


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
        member_organization_id (Optional[str]): The organization the
            member's account belongs to: yours, or another one, such as a
            workforce provider's or, if you are a workforce provider, a
            customer's. It is the same whoever asks. ``None`` if the account
            no longer exists.
        member_organization_name (Optional[str]): That organization's name,
            or ``org.name.<id>`` if it is masked for you. ``None`` if the
            organization can no longer be found.
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
    member_organization_id: Optional[str] = None
    member_organization_name: Optional[str] = None
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
        member_organization_id (Optional[str]): The organization the
            member's account belongs to: yours, or another one, such as a
            workforce provider's or, if you are a workforce provider, a
            customer's. It is the same whoever asks. ``None`` if the account
            no longer exists.
        member_organization_name (Optional[str]): That organization's name,
            or ``org.name.<id>`` if it is masked for you. ``None`` if the
            organization can no longer be found.
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
    member_organization_id: Optional[str] = None
    member_organization_name: Optional[str] = None
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
        member_organization_id (Optional[str]): The organization the
            member's account belongs to: yours, or another one, such as a
            workforce provider's or, if you are a workforce provider, a
            customer's. It is the same whoever asks. ``None`` if the account
            no longer exists.
        member_organization_name (Optional[str]): That organization's name,
            or ``org.name.<id>`` if it is masked for you. ``None`` if the
            organization can no longer be found.
        project_id (str)
        project_name (Optional[str]): ``None`` for a project that can no
            longer be found. Its figures are still counted.
        project_organization_id (Optional[str]): The organization that owns
            the project. It differs from yours for a project shared with you,
            and is ``None`` for a project that can no longer be found.
        project_organization_name (Optional[str])
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
    member_organization_id: Optional[str] = None
    member_organization_name: Optional[str] = None
    project_id: str
    project_name: Optional[str] = None
    project_organization_id: Optional[str] = None
    project_organization_name: Optional[str] = None
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


class SignInSession(_CamelCaseMixin):
    """One sign-in session of a member of your organization.

    A session is one sign-in in one browser, or a switch into this workspace
    from the same person's user in another one. It lasts until the member
    signs out, until Labelbox ends it (a new sign-in in the same browser, a
    switch to another workspace, the member's removal) or, when neither
    happened, until every credential the sign-in issued has lapsed. That
    last end is derived when the session is read, and is the latest the
    session could last: it is not when the member stopped working.

    Attributes:
        session_id (str): The session's ID. Its events in
            :meth:`labelbox.Client.get_sign_in_events` carry it too.
        user_id (str)
        email (Optional[str]): ``None`` if the user no longer exists or is
            now another organization's.
        member_deleted (bool): True if the member was deactivated, no longer
            exists, or is now another organization's. A session stays with
            the organization it started in.
        started_at (datetime): When the member signed in, or switched into
            this workspace.
        start_kind (str): How the session started: ``"SIGN_IN"`` or
            ``"WORKSPACE_SWITCH"`` (see :class:`SignInStartKind`).
        status (str): ``"OPEN"`` or ``"ENDED"`` (see
            :class:`SignInSessionStatus`).
        ended_at (Optional[datetime]): When the session ended, by a recorded
            or a derived end. For a derived end it is ``expires_at``.
            ``None`` while the session is open.
        end_reason (Optional[str]): How the session ended (see
            :class:`SignInEndReason`). ``None`` while it is open.
        end_derived (Optional[bool]): True when nothing recorded the end.
            ``end_reason`` is then ``"MAX_DURATION_REACHED"`` and
            ``ended_at`` is ``expires_at``: the moment the session could
            last no longer, not when the member stopped working. ``None``
            while the session is open.
        expires_at (datetime): The latest the session can end. That is
            normally 84 hours and a minute after the sign-in (the sign-in
            cookie's lifetime, plus a minute), or 7 days after a switch made
            where the organization uses tokens instead of cookies. Opening a
            workspace link again, or connecting an application to the
            account, sets the cookie again, so while the session is open
            ``expires_at`` can still move later. Once it has passed, it does
            not change.
        duration_seconds (Optional[int]): Whole seconds from start to end.
            ``None`` while the session is open. Sessions record sign-ins and
            how they ended, not activity, so no duration is time worked,
            recorded end or not. For example, a derived end counts all the
            time the session could have lasted, a sign-out the next morning
            counts the night, and overlapping sessions in two browsers both
            count.
    """

    session_id: str
    user_id: str
    email: Optional[str] = None
    member_deleted: bool
    started_at: datetime
    start_kind: str
    status: str
    ended_at: Optional[datetime] = None
    end_reason: Optional[str] = None
    end_derived: Optional[bool] = None
    expires_at: datetime
    duration_seconds: Optional[int] = None


class SignInEvent(_CamelCaseMixin):
    """A sign-in or a sign-out of a member of your organization.

    A sign-in happens when a session starts and a sign-out when it ends, by
    a recorded or a derived end (see :class:`SignInSession`).

    Attributes:
        event_id (str): The same on every read, to drop events already seen.
        type (str): ``"SIGN_IN"`` or ``"SIGN_OUT"`` (see
            :class:`SignInEventType`).
        occurred_at (datetime): When it happened: a sign-in when its session
            started, a sign-out when it ended.
        session_id (str): The session it starts or ends.
        user_id (str)
        email (Optional[str]): ``None`` if the user no longer exists or is
            now another organization's.
        start_kind (Optional[str]): How the session started (see
            :class:`SignInStartKind`). ``None`` for a sign-out.
        end_reason (Optional[str]): How the session ended (see
            :class:`SignInEndReason`). ``None`` for a sign-in.
        end_derived (Optional[bool]): True for a sign-out nothing recorded.
            ``end_reason`` is then ``"MAX_DURATION_REACHED"`` and the
            sign-out is at the session's ``expires_at``: the moment the
            session could last no longer, not when the member stopped
            working. ``None`` for a sign-in.
        session_started_at (datetime): When the session started. For a
            sign-in, it is ``occurred_at``.
    """

    event_id: str
    type: str
    occurred_at: datetime
    session_id: str
    user_id: str
    email: Optional[str] = None
    start_kind: Optional[str] = None
    end_reason: Optional[str] = None
    end_derived: Optional[bool] = None
    session_started_at: datetime


class PerformanceTableChangedError(LabelboxError):
    """A table changed while its pages were being read.

    Raised while iterating :class:`PerformanceRows` when a page reports a
    different ``total`` from the first page. Iterate the table again.
    """


Row = TypeVar("Row", bound=_CamelCaseMixin)


class PerformanceRows(Generic[Row]):
    """The rows of a performance table.

    Iterating fetches the table a page at a time, so a large table is never
    held in one response. Nothing is requested until the rows, ``total`` or
    ``cached_at`` are read. The rows come in a fixed order.

    Each page is a separate request, so the pages fit together only if the
    table does not change between them. A workspace table read with the
    cache on is cut from a reading of the report that is kept for five
    minutes from when it was taken, possibly by an earlier request, so its
    pages agree while that reading lasts. A very large table is not kept,
    and an iteration that outlasts the reading continues from a new one. A
    project table is read a page at a time, and on any table, who is in the
    groups of a ``user_group_ids`` filter is worked out again for every
    page. If the figures or a group's members change between pages, a row
    can be missed or repeated.

    When a page reports a different ``total`` from the first page, iterating
    raises :class:`PerformanceTableChangedError`: read the table again. A
    change that leaves the number of rows as it was cannot be seen this way,
    such as one member joining a group as another with as many rows leaves.

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
        total: Optional[int] = None
        while True:
            page = self._page(number)
            if total is None:
                total = int(page["total"])
            elif int(page["total"]) != total:
                raise PerformanceTableChangedError(
                    f"The table changed while it was read: page 1 counted "
                    f"{total} rows and page {number} counts {page['total']}. "
                    "Read it again."
                )
            rows = page["data"]
            for row in rows:
                yield self._row_type.model_validate(row)
            seen += len(rows)
            if not rows or seen >= total:
                return
            number += 1


class PerformanceCursorRows(Generic[Row]):
    """Rows the API pages by cursor: sign-in sessions and sign-in events.

    Iterating fetches the rows a page at a time, each page from where the
    one before ended, until the API says there are no more. Nothing is
    requested until the rows are read. The rows come in a fixed order.
    Unlike :class:`PerformanceRows` there is no ``total``: the API does not
    count the rows.

    Each page is a separate request that continues after the last row of
    the page before, so the pages never overlap. A row on a later page is as
    it was when that page was read: a session that ended meanwhile is listed
    as ended, and is left out of a reading of open sessions. Who is in the
    groups of a ``user_group_ids`` filter is worked out again for every
    page.

    Iterating a second time reads the rows again from the first page.

    >>> for session in client.get_sign_in_sessions("2026-11-02", "2026-11-08"):
    ...     print(session.email, session.started_at, session.end_reason)
    """

    def __init__(
        self,
        fetch_page: Callable[[Optional[str]], Dict[str, Any]],
        row_type: Type[Row],
    ):
        self._fetch_page = fetch_page
        self._row_type = row_type
        # The last page of the latest reading, once it got there.
        self._last_page: Optional[Dict[str, Any]] = None

    def __iter__(self) -> Iterator[Row]:
        self._last_page = None
        cursor: Optional[str] = None
        while True:
            page = self._fetch_page(cursor)
            for row in page["data"]:
                yield self._row_type.model_validate(row)
            cursor = page.get("nextCursor")
            if not cursor:
                self._last_page = page
                return


class SignInEventRows(PerformanceCursorRows[SignInEvent]):
    """The sign-ins and sign-outs of :meth:`labelbox.Client.get_sign_in_events`.

    The events are fetched a page at a time as you iterate, as for
    :class:`PerformanceCursorRows`, ordered by ``occurred_at``.

    The feed stops at ``complete_through``. Read it to the end and keep
    ``complete_through``: every event before it has been listed. To follow
    the feed, read it again next time from the day an hour before the
    ``complete_through`` you kept, and drop the events whose ``event_id``
    you have already seen. That also picks up an event that took unusually
    long to be recorded.

    >>> from datetime import datetime, timedelta, timezone
    >>> events = client.get_sign_in_events("2026-11-03", "2026-11-09")
    >>> seen = {event.event_id for event in events}
    >>> since = events.complete_through - timedelta(hours=1)
    >>> # Next time:
    >>> for event in client.get_sign_in_events(since, datetime.now(timezone.utc)):
    ...     if event.event_id not in seen:
    ...         seen.add(event.event_id)
    ...         print(event.occurred_at, event.email, event.type)
    """

    def __init__(self, fetch_page: Callable[[Optional[str]], Dict[str, Any]]):
        super().__init__(fetch_page, SignInEvent)

    @property
    def complete_through(self) -> Optional[datetime]:
        """Where the feed stops, as the last page reports it.

        The earlier of the end of ``end_date`` and five minutes before the
        last page was read. Every event before it is in the feed, and a
        derived sign-out is listed once its time is before it; events at or
        after it are not listed yet.

        It is taken from the last page, the one with no next page, so it is
        ``None`` until the events have been read to the end. Iterating again
        resets it, and it then describes that reading.
        """
        if self._last_page is None:
            return None
        return _parse_datetime(self._last_page["completeThrough"])


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


def _to_status(
    status: Optional[Union[SignInSessionStatus, str]],
) -> Optional[str]:
    """A session status as the filter takes it: ``open`` or ``ended``.

    A session's own status is in capitals, like SignInSessionStatus, and the
    filter is in lower case, so either spelling is accepted.
    """
    if status is None:
        return None
    value = status.value if isinstance(status, Enum) else status
    return value.lower()


def _to_event_types(
    types: Optional[Iterable[Union[SignInEventType, str]]],
) -> Optional[str]:
    """Event types as one comma-separated parameter.

    ``None`` lists both kinds. An empty list is refused, as the API refuses
    it, before anything is requested.
    """
    if types is None:
        return None
    if isinstance(types, str):
        types = [types]
    values = [
        str(value.value) if isinstance(value, Enum) else value
        for value in types
    ]
    if not values:
        raise ValueError(
            "types is empty. Pass None to list both sign-ins and sign-outs."
        )
    return ",".join(values)


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
    member_organization_ids: Optional[Iterable[Any]] = None,
    user_group_ids: Optional[Iterable[Any]] = None,
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
        memberOrganizationIds=_to_ids(
            "member_organization_ids", member_organization_ids
        ),
        userGroupIds=_to_ids("user_group_ids", user_group_ids),
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
    member_organization_ids: Optional[Iterable[Any]] = None,
    user_group_ids: Optional[Iterable[Any]] = None,
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
        memberOrganizationIds=_to_ids(
            "member_organization_ids", member_organization_ids
        ),
        userGroupIds=_to_ids("user_group_ids", user_group_ids),
        useCache=None if use_cache else False,
    )


def _cursor_pages(
    client: "Client", path: str, **params: Any
) -> Callable[[Optional[str]], Dict[str, Any]]:
    """Fetches one page of a listing paged by cursor: the first without one."""

    def fetch_page(cursor: Optional[str]) -> Dict[str, Any]:
        # Sent as the page before returned it: a cursor is not to be read.
        return _get(client, path, **params, cursor=cursor)

    return fetch_page


def get_sign_in_sessions(
    client: "Client",
    start_date: DateLike,
    end_date: DateLike,
    user_ids: Optional[Iterable[Any]] = None,
    user_group_ids: Optional[Iterable[Any]] = None,
    status: Optional[Union[SignInSessionStatus, str]] = None,
    page_size: int = _SIGN_IN_PAGE_SIZE,
) -> PerformanceCursorRows[SignInSession]:
    fetch_page = _cursor_pages(
        client,
        "/workspace/sign-in-sessions",
        **_period(start_date, end_date),
        userIds=_to_ids("user_ids", user_ids),
        userGroupIds=_to_ids("user_group_ids", user_group_ids),
        status=_to_status(status),
        perPage=page_size,
    )
    return PerformanceCursorRows(fetch_page, SignInSession)


def get_sign_in_events(
    client: "Client",
    start_date: DateLike,
    end_date: DateLike,
    user_ids: Optional[Iterable[Any]] = None,
    user_group_ids: Optional[Iterable[Any]] = None,
    types: Optional[Iterable[Union[SignInEventType, str]]] = None,
    include_derived: bool = True,
    page_size: int = _SIGN_IN_PAGE_SIZE,
) -> SignInEventRows:
    fetch_page = _cursor_pages(
        client,
        "/workspace/sign-in-events",
        **_period(start_date, end_date),
        userIds=_to_ids("user_ids", user_ids),
        userGroupIds=_to_ids("user_group_ids", user_group_ids),
        types=_to_event_types(types),
        # Only sent to leave derived sign-outs out; they are in by default.
        includeDerived=None if include_derived else False,
        perPage=page_size,
    )
    return SignInEventRows(fetch_page)
