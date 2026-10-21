"""User group audit log.

Labelbox records an event each time a person is added to a user group,
removed from it or given a new role in it, each time the group is attached to
or detached from a project, and when the group is deleted. Each event says who
made the change, whether a person or an automation made it, and how it reached
Labelbox (the app, the API, the Labelbox MCP, a CSV upload, a background task
or Labelbox itself). Events are never changed or deleted. The log starts when
it shipped; earlier changes are not in it.

Only people who can manage a group can read its events.

The methods on :class:`labelbox.schema.user_group.UserGroup` that return the
classes below are thin wrappers over the function at the bottom of this module.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, Iterable, Optional, Union

from labelbox.pagination import PaginatedCollection
from labelbox.utils import _CamelCaseMixin

if TYPE_CHECKING:
    from labelbox import Client

# The API returns at most 100 events per page.
_MAX_PAGE_SIZE = 100

DateTimeLike = Union[datetime, str]
"""A moment: a ``datetime`` (naive ones are read as UTC) or an ISO 8601 string."""


class UserGroupAuditEventType(str, Enum):
    """What a group audit event records."""

    #: A person was added to the group.
    MEMBER_ADDED = "MEMBER_ADDED"
    #: A person was removed from the group.
    MEMBER_REMOVED = "MEMBER_REMOVED"
    #: A member's role in the group changed. One event, not a removal and an
    #: addition.
    MEMBER_ROLE_CHANGED = "MEMBER_ROLE_CHANGED"
    #: The group was attached to a project: its members gained access to it.
    GROUP_ATTACHED_TO_PROJECT = "GROUP_ATTACHED_TO_PROJECT"
    #: The group was detached from a project: its members lost access
    #: through it.
    GROUP_DETACHED_FROM_PROJECT = "GROUP_DETACHED_FROM_PROJECT"
    #: The group was deleted.
    GROUP_DELETED = "GROUP_DELETED"


class UserGroupAuditActorKind(str, Enum):
    """Whether a person or an automation made a group change."""

    #: A person, in the Labelbox app.
    PERSON = "PERSON"
    #: An automation: the API with an API key (the SDK and scripts), the
    #: Labelbox MCP, a background task, or Labelbox itself.
    AUTOMATION = "AUTOMATION"


class UserGroupAuditChannel(str, Enum):
    """How a group change reached Labelbox."""

    #: The Labelbox app.
    APP = "APP"
    #: The API with an API key: the SDK and scripts.
    API = "API"
    #: The Labelbox MCP.
    MCP = "MCP"
    #: A CSV of members uploaded to the group.
    CSV_IMPORT = "CSV_IMPORT"
    #: The Alignerr API.
    ALIGNERR_API = "ALIGNERR_API"
    #: A background task whose requester is not known.
    BACKGROUND_TASK = "BACKGROUND_TASK"
    #: Labelbox itself, with no requester: for example removing a deleted
    #: user from their groups.
    SYSTEM = "SYSTEM"


class UserGroupAuditEvent(_CamelCaseMixin):
    """One change to a user group.

    Attributes:
        id (str): Stable ID of the event.
        group_id (str): The group's ID.
        group_name (Optional[str]): The group's current name. ``None`` once
            the group is deleted.
        type (str): What changed (see :class:`UserGroupAuditEventType`).
            Unknown values are kept as strings.
        occurred_at (datetime): When the change was made.
        actor_kind (str): Whether a person or an automation made the change
            (see :class:`UserGroupAuditActorKind`).
        channel (str): How the change reached Labelbox (see
            :class:`UserGroupAuditChannel`).
        actor_user_id (Optional[str]): The person who made the change, or the
            user an automation acted for (the API key's owner, the MCP user,
            the task's requester). ``None`` when Labelbox made the change
            itself.
        automation (Optional[str]): Which automation made the change: the API
            key, MCP client, task or reason. ``None`` for a person.
        member_user_id (Optional[str]): The person added, removed or given a
            new role. ``None`` for project and group events.
        previous_role_id (Optional[str]): The member's role before a removal
            or role change.
        previous_role_name (Optional[str]): That role's name.
        role_id (Optional[str]): The member's role after an addition or role
            change.
        role_name (Optional[str]): That role's name.
        project_id (Optional[str]): The project the group was attached to or
            detached from.
        project_name (Optional[str]): That project's name.
    """

    id: str
    group_id: str
    group_name: Optional[str] = None
    type: Union[UserGroupAuditEventType, str]
    occurred_at: datetime
    actor_kind: Union[UserGroupAuditActorKind, str]
    channel: Union[UserGroupAuditChannel, str]
    actor_user_id: Optional[str] = None
    automation: Optional[str] = None
    member_user_id: Optional[str] = None
    previous_role_id: Optional[str] = None
    previous_role_name: Optional[str] = None
    role_id: Optional[str] = None
    role_name: Optional[str] = None
    project_id: Optional[str] = None
    project_name: Optional[str] = None


_FIELDS = """
    id groupId groupName type occurredAt actorKind channel actorUserId
    automation memberUserId previousRoleId previousRoleName roleId roleName
    projectId projectName
"""


def _to_id(name: str, value: Any) -> Optional[str]:
    if value is None:
        return None
    uid = getattr(value, "uid", None) or getattr(value, "id", None) or value
    if not isinstance(uid, str) or not uid:
        raise ValueError(f"{name} must be an ID or an SDK object with one")
    return uid


def _to_datetime(
    name: str, value: Optional[DateTimeLike]
) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError(
                f"{name} must be a datetime or an ISO 8601 string"
            ) from error
    if not isinstance(value, datetime):
        raise ValueError(f"{name} must be a datetime or an ISO 8601 string")
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _iso(value: Optional[datetime]) -> Optional[str]:
    return (
        value.isoformat(timespec="milliseconds").replace("+00:00", "Z")
        if value
        else None
    )


def _known(enum: Any, value: Any) -> Any:
    return enum(value) if value in enum._value2member_map_ else value


def _to_event(result: Dict[str, Any]) -> UserGroupAuditEvent:
    return UserGroupAuditEvent.model_validate(
        {
            **result,
            "type": _known(UserGroupAuditEventType, result.get("type")),
            "actorKind": _known(
                UserGroupAuditActorKind, result.get("actorKind")
            ),
            "channel": _known(UserGroupAuditChannel, result.get("channel")),
        }
    )


def get_user_group_audit_events(
    client: "Client",
    group: Any = None,
    member: Any = None,
    actor: Any = None,
    actor_kind: Optional[Union[UserGroupAuditActorKind, str]] = None,
    types: Optional[Iterable[Union[UserGroupAuditEventType, str]]] = None,
    project: Any = None,
    occurred_after: Optional[DateTimeLike] = None,
    occurred_before: Optional[DateTimeLike] = None,
    page_size: int = _MAX_PAGE_SIZE,
) -> PaginatedCollection:
    if not isinstance(page_size, int) or not 1 <= page_size <= _MAX_PAGE_SIZE:
        raise ValueError(f"page_size must be between 1 and {_MAX_PAGE_SIZE}")
    after = _to_datetime("occurred_after", occurred_after)
    before = _to_datetime("occurred_before", occurred_before)
    if after and before and after >= before:
        raise ValueError("occurred_after must be before occurred_before")
    where = {
        key: value
        for key, value in {
            "groupId": _to_id("group", group),
            "memberUserId": _to_id("member", member),
            "actorUserId": _to_id("actor", actor),
            "actorKind": UserGroupAuditActorKind(actor_kind).value
            if actor_kind is not None
            else None,
            "types": [UserGroupAuditEventType(t).value for t in types]
            if types is not None
            else None,
            "projectId": _to_id("project", project),
            "occurredAfter": _iso(after),
            "occurredBefore": _iso(before),
        }.items()
        if value is not None
    }
    query = (
        """query GetUserGroupAuditEventsPyApi(
        $where: UserGroupAuditEventsWhereInput, $first: Int, $from: String
    ) {
        userGroupAuditEvents(where: $where, first: $first, after: $from) {
            nodes { %s }
            nextCursor
        }
    }"""
        % _FIELDS
    )
    # The input object is a nested dict: PaginatedCollection only types
    # scalars.
    params: Dict[str, Any] = {"where": where, "first": page_size}
    return PaginatedCollection(
        client=client,
        query=query,
        params=params,
        dereferencing=["userGroupAuditEvents", "nodes"],
        obj_class=lambda _, result: _to_event(result),
        cursor_path=["userGroupAuditEvents", "nextCursor"],
    )
