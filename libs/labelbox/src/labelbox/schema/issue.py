"""Issue and Comment models for the Labelbox Python SDK.

Uses ``_CamelCaseMixin`` (Pydantic) instead of ``DbObject`` / ``Updateable``
/ ``Deletable`` because the backend's GraphQL mutations use typed input objects
incompatible with the ORM's auto-generated mutations.
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, List, Optional

from pydantic import ConfigDict, PrivateAttr

from labelbox.orm.model import Entity
from labelbox.schema.issue_category import IssueCategory
from labelbox.schema.issue_position import (
    IssuePosition,
    _deserialize_position,
)
from labelbox.schema.user import User
from labelbox.utils import _CamelCaseMixin

if TYPE_CHECKING:
    from labelbox.schema.data_row import DataRow
    from labelbox.schema.label import Label


class IssueStatus(str, Enum):
    """Status of an issue."""

    OPEN = "Open"
    RESOLVED = "Resolved"


# ---------------------------------------------------------------------------
# GraphQL fragments
# ---------------------------------------------------------------------------

_USER_FIELDS = (
    "id email nickname name picture isViewer isExternalUser "
    "createdAt updatedAt lastLoginAt"
)

_COMMENT_FIELDS = (
    """
    id
    content
    createdBy { %s }
    createdAt
    updatedAt
"""
    % _USER_FIELDS
)

_ISSUE_FIELDS = """
    id
    friendlyId
    labelId
    dataRowId
    categoryId
    content
    position
    status
    createdBy { %s }
    resolvedBy { %s }
    createdAt
    updatedAt
    resolvedAt
    contentUpdatedAt
    latestReplyAt
""" % (_USER_FIELDS, _USER_FIELDS)


# ---------------------------------------------------------------------------
# Helper: build a User DbObject from a raw dict
# ---------------------------------------------------------------------------


def _build_user(client: Any, raw: Optional[dict]) -> Optional[User]:
    """Construct a :class:`User` DbObject from a GraphQL response fragment.

    Returns ``None`` when *raw* is ``None``.
    """
    if raw is None:
        return None
    return User(client, raw)


# ---------------------------------------------------------------------------
# Comment
# ---------------------------------------------------------------------------


class Comment(_CamelCaseMixin):
    """A comment attached to an :class:`Issue`.

    Attributes:
        id: Unique identifier.
        content: Comment body text.
        created_by: The :class:`~labelbox.schema.user.User` who authored the
            comment.
        created_at: Creation timestamp.
        updated_at: Last-modification timestamp.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
    )

    id: str
    content: str
    created_by: Any  # User DbObject
    created_at: datetime
    updated_at: datetime
    _client: Any = PrivateAttr(default=None)

    def __repr__(self) -> str:
        return "<Comment ID: %s>" % self.id

    def update(self, content: str) -> "Comment":
        """Update this comment's content.

        Args:
            content: New body text.

        Returns:
            Updated :class:`Comment` instance.
        """
        query_str = (
            """mutation UpdateCommentPyApi(
            $where: WhereUniqueIdInput!,
            $data: UpdateCommentInput!
        ) {
            updateComment(where: $where, data: $data) { %s }
        }"""
            % _COMMENT_FIELDS
        )

        result = self._client.execute(
            query_str,
            {
                "where": {"id": self.id},
                "data": {"content": content},
            },
            experimental=True,
        )
        return _parse_comment(self._client, result["updateComment"])

    def delete(self) -> bool:
        """Delete this comment.

        Returns:
            ``True`` when the deletion succeeds.
        """
        query_str = """mutation DeleteCommentPyApi(
            $where: WhereUniqueIdInput!
        ) {
            deleteComment(where: $where)
        }"""

        self._client.execute(
            query_str, {"where": {"id": self.id}}, experimental=True
        )
        return True


# ---------------------------------------------------------------------------
# Issue
# ---------------------------------------------------------------------------


class Issue(_CamelCaseMixin):
    """An issue pinned to a data row within a project.

    Attributes:
        id: Unique identifier.
        friendly_id: Human-readable short identifier.
        label_id: Associated label ID (may be ``None``).
        data_row_id: Associated data-row ID (may be ``None`` for legacy
            issues).
        category_id: Associated issue-category ID (may be ``None``).
        content: Issue body text.
        position: Typed position model or ``None``.
        status: :class:`IssueStatus` (``OPEN`` / ``RESOLVED``).
        created_by: The :class:`~labelbox.schema.user.User` who created the
            issue.
        resolved_by: The :class:`~labelbox.schema.user.User` who resolved it,
            or ``None``.
        created_at: Creation timestamp.
        updated_at: Last-modification timestamp.
        resolved_at: Resolution timestamp, or ``None``.
        content_updated_at: Timestamp of last content edit, or ``None``.
        latest_reply_at: Timestamp of the most recent comment, or ``None``.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
    )

    id: str
    friendly_id: str
    label_id: Optional[str] = None
    data_row_id: Optional[str] = None
    category_id: Optional[str] = None
    content: str
    position: Optional[Any] = None  # IssuePosition (typed at runtime)
    status: IssueStatus
    created_by: Any  # User DbObject
    resolved_by: Optional[Any] = None  # User DbObject or None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    content_updated_at: Optional[datetime] = None
    latest_reply_at: Optional[datetime] = None
    _project_id: Optional[str] = PrivateAttr(default=None)
    _client: Any = PrivateAttr(default=None)

    def __repr__(self) -> str:
        return "<Issue ID: %s>" % self.id

    # ------------------------------------------------------------------
    # Methods that fetch related objects (each makes an API call)
    # ------------------------------------------------------------------

    def comments(self) -> List[Comment]:
        """Fetch all comments for this issue.

        Returns:
            List of :class:`Comment` instances.
        """
        query_str = (
            """query GetIssueCommentsPyApi($where: WhereUniqueIdInput!) {
            issue(where: $where) {
                comments { %s }
            }
        }"""
            % _COMMENT_FIELDS
        )

        result = self._client.execute(
            query_str, {"where": {"id": self.id}}, experimental=True
        )
        raw_comments = result.get("issue", {}).get("comments", [])
        return [_parse_comment(self._client, c) for c in raw_comments]

    def data_row(self) -> Optional["DataRow"]:
        """Fetch the associated :class:`~labelbox.schema.data_row.DataRow`.

        Returns:
            The data row, or ``None`` if :attr:`data_row_id` is not set.
        """
        if self.data_row_id is None:
            return None
        return self._client.get_data_row(self.data_row_id)

    def category(self) -> Optional[IssueCategory]:
        """Fetch the associated :class:`IssueCategory`.

        Requires :attr:`project_id` to be set (automatically populated
        when the issue is obtained via :class:`Project` methods).

        Returns:
            The category, or ``None`` if :attr:`category_id` is not set
            or the project context is unavailable.
        """
        if self.category_id is None:
            return None
        if self._project_id is None:
            return None

        query_str = """query GetIssueCategoriesPyApi($projectId: ID!) {
            project(where: {id: $projectId}) {
                issueCategories { id name description }
            }
        }"""

        result = self._client.execute(
            query_str, {"projectId": self._project_id}
        )
        raw_list = result.get("project", {}).get("issueCategories", [])
        for raw in raw_list:
            if raw["id"] == self.category_id:
                cat = IssueCategory(
                    id=raw["id"],
                    name=raw["name"],
                    description=raw["description"],
                )
                cat._client = self._client
                return cat
        return None

    def label(self) -> Optional["Label"]:
        """Fetch the associated :class:`~labelbox.schema.label.Label`.

        Returns:
            The label, or ``None`` if :attr:`label_id` is not set.
        """
        if self.label_id is None:
            return None
        return self._client._get_single(Entity.Label, self.label_id)

    # ------------------------------------------------------------------
    # Mutation methods
    # ------------------------------------------------------------------

    def update(
        self,
        content: Optional[str] = None,
        category_id: Optional[str] = None,
        position: Optional[IssuePosition] = None,
        label_id: Optional[str] = None,
    ) -> "Issue":
        """Update this issue.

        Only the provided fields are modified; pass ``None`` to leave a
        field unchanged.

        Args:
            content: New body text.
            category_id: New category ID.
            position: New position model.
            label_id: New label ID.

        Returns:
            Updated :class:`Issue` instance.
        """
        data: dict = {}
        if content is not None:
            data["content"] = content
        if category_id is not None:
            data["categoryId"] = category_id
        if position is not None:
            data["position"] = position.to_dict()
        if label_id is not None:
            data["labelId"] = label_id

        if not data:
            return self

        query_str = (
            """mutation UpdateIssuePyApi(
            $where: WhereUniqueIdInput!,
            $data: UpdateIssueInput!
        ) {
            updateIssue(where: $where, data: $data) { %s }
        }"""
            % _ISSUE_FIELDS
        )

        result = self._client.execute(
            query_str,
            {"where": {"id": self.id}, "data": data},
            experimental=True,
        )
        return _parse_issue(
            self._client, result["updateIssue"], project_id=self._project_id
        )

    def delete(self) -> bool:
        """Delete this issue.

        Returns:
            ``True`` when the deletion succeeds.
        """
        query_str = """mutation DeleteIssuePyApi($data: DeleteIssueInput!) {
            deleteIssue(data: $data)
        }"""

        self._client.execute(
            query_str,
            {"data": {"issueIds": [self.id]}},
            experimental=True,
        )
        return True

    def resolve(self) -> "Issue":
        """Resolve this issue.

        Returns:
            Updated :class:`Issue` with ``status == IssueStatus.RESOLVED``.
        """
        query_str = (
            """mutation ResolveIssuePyApi($where: WhereUniqueIdInput!) {
            resolveIssue(where: $where) { %s }
        }"""
            % _ISSUE_FIELDS
        )

        result = self._client.execute(
            query_str, {"where": {"id": self.id}}, experimental=True
        )
        return _parse_issue(
            self._client, result["resolveIssue"], project_id=self._project_id
        )

    def reopen(self) -> "Issue":
        """Re-open this issue.

        Returns:
            Updated :class:`Issue` with ``status == IssueStatus.OPEN``.
        """
        query_str = (
            """mutation OpenIssuePyApi($where: WhereUniqueIdInput!) {
            openIssue(where: $where) { %s }
        }"""
            % _ISSUE_FIELDS
        )

        result = self._client.execute(
            query_str, {"where": {"id": self.id}}, experimental=True
        )
        return _parse_issue(
            self._client, result["openIssue"], project_id=self._project_id
        )

    def create_comment(self, content: str) -> Comment:
        """Create a new comment on this issue.

        Args:
            content: Comment body text.

        Returns:
            The newly created :class:`Comment`.
        """
        query_str = (
            """mutation CreateCommentPyApi($data: CreateCommentInput!) {
            createComment(data: $data) { %s }
        }"""
            % _COMMENT_FIELDS
        )

        result = self._client.execute(
            query_str,
            {"data": {"content": content, "issueId": self.id}},
            experimental=True,
        )
        return _parse_comment(self._client, result["createComment"])


# ---------------------------------------------------------------------------
# Factory functions
# ---------------------------------------------------------------------------


def _parse_comment(client: Any, data: dict) -> Comment:
    """Build a :class:`Comment` from a raw GraphQL response dict."""
    created_by = _build_user(client, data.get("createdBy"))
    comment = Comment(
        id=data["id"],
        content=data["content"],
        created_by=created_by,
        created_at=data["createdAt"],
        updated_at=data["updatedAt"],
    )
    comment._client = client
    return comment


def _parse_issue(
    client: Any, data: dict, project_id: Optional[str] = None
) -> Issue:
    """Build an :class:`Issue` from a raw GraphQL response dict."""
    created_by = _build_user(client, data.get("createdBy"))
    resolved_by = _build_user(client, data.get("resolvedBy"))
    position = _deserialize_position(data.get("position"))

    issue = Issue(
        id=data["id"],
        friendly_id=data["friendlyId"],
        label_id=data.get("labelId"),
        data_row_id=data.get("dataRowId"),
        category_id=data.get("categoryId"),
        content=data["content"],
        position=position,
        status=IssueStatus(data["status"]),
        created_by=created_by,
        resolved_by=resolved_by,
        created_at=data["createdAt"],
        updated_at=data["updatedAt"],
        resolved_at=data.get("resolvedAt"),
        content_updated_at=data.get("contentUpdatedAt"),
        latest_reply_at=data.get("latestReplyAt"),
    )
    issue._client = client
    issue._project_id = project_id
    return issue
