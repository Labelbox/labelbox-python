"""Label version history.

Labelbox records a version of a label at each hand-off: when the label is
submitted or saved from the editor, approved or rejected in a review step,
submitted from a rework step, or moved into a rework step. Each version holds
who made the hand-off, when, in which workflow step, and the label's
annotations at that moment. Autosaves and drafts record no versions, and
versions are never changed or deleted.

The methods on :class:`labelbox.Client`, :class:`labelbox.schema.project.Project`
and :class:`labelbox.schema.label.Label` that return the classes below are thin
wrappers over the functions at the bottom of this module.
"""

import json
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from labelbox.pagination import PaginatedCollection
from labelbox.utils import _CamelCaseMixin

if TYPE_CHECKING:
    from labelbox import Client

# The API returns at most 100 versions per page.
_MAX_PAGE_SIZE = 100

DateTimeLike = Union[datetime, str]
"""A moment: a ``datetime`` (naive ones are read as UTC) or an ISO 8601 string."""


class LabelVersionAction(str, Enum):
    """The hand-off a label version records."""

    #: The label was created from the editor: a labeler's submit.
    SUBMITTED = "SUBMITTED"
    #: An existing label was saved from the editor: a reviewer's edit in a
    #: review step, a labeler's edit in a rework step, or a later save.
    SAVED = "SAVED"
    #: A reviewer approved the label in a review step.
    APPROVED = "APPROVED"
    #: A reviewer rejected the label in a review step.
    REJECTED = "REJECTED"
    #: The data row was submitted from a rework step.
    REWORK_SUBMITTED = "REWORK_SUBMITTED"
    #: The data row was moved into a rework step by hand.
    SENT_TO_REWORK = "SENT_TO_REWORK"


class LabelVersionStage(_CamelCaseMixin):
    """The workflow step a label version was recorded in, as it was then.

    Attributes:
        task_queue_id (str): The step's task queue ID.
        name (Optional[str]): The step's name when the version was recorded.
        type (Optional[str]): The step's type, for example
            ``"MANUAL_REVIEW_QUEUE"`` or ``"MANUAL_REWORK_QUEUE"``.
    """

    task_queue_id: str
    name: Optional[str] = None
    type: Optional[str] = None


class LabelVersion(_CamelCaseMixin):
    """One recorded version of a label.

    Attributes:
        id (str): The version's ID. It never changes.
        label_id (str)
        data_row_id (str)
        project_id (str)
        action (str): The hand-off (see :class:`LabelVersionAction`).
            Unknown values are kept as strings.
        created_at (datetime): When the version was recorded.
        created_by_id (str): The user who made the hand-off: the labeler for
            a submit, the reviewer for a review save or decision.
        stage (Optional[LabelVersionStage]): The workflow step the data row
            was in. ``None`` when it was in none (Done).
        annotation_count (int): Number of annotations in the version, counted
            as the editor and exports count them: each object and each
            classification at the top of the label. A classification's
            answers and an object's nested classifications are part of it,
            and the segmentation group that holds masks is not counted.
        label (Optional[str]): The annotations at that moment, as stringified
            JSON in the same shape as :attr:`labelbox.schema.label.Label.label`.
            Feature schema names are the ones in effect then. ``None`` when
            read with ``include_annotations=False``.
        label_json (Optional[dict]): ``label`` parsed.
    """

    id: str
    label_id: str
    data_row_id: str
    project_id: str
    action: Union[LabelVersionAction, str]
    created_at: datetime
    created_by_id: str
    stage: Optional[LabelVersionStage] = None
    annotation_count: int
    label: Optional[str] = None
    label_json: Optional[Dict[str, Any]] = None


_FIELDS = """
    id labelId dataRowId projectId action createdAt createdById
    stage { taskQueueId name type }
    annotationCount
"""
_ANNOTATION_FIELDS = "label labelJson"


def _fields(include_annotations: bool) -> str:
    return _FIELDS + (_ANNOTATION_FIELDS if include_annotations else "")


def _to_id(name: str, value: Any) -> Optional[str]:
    if value is None:
        return None
    uid = getattr(value, "uid", value)
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


def _to_version(result: Dict[str, Any]) -> LabelVersion:
    label_json = result.get("labelJson")
    if isinstance(label_json, str):
        label_json = json.loads(label_json)
    action = result.get("action")
    if action in LabelVersionAction._value2member_map_:
        action = LabelVersionAction(action)
    return LabelVersion.model_validate(
        {**result, "labelJson": label_json, "action": action}
    )


def get_label_versions(
    client: "Client",
    project_id: str,
    label: Any = None,
    data_row: Any = None,
    created_by: Any = None,
    created_after: Optional[DateTimeLike] = None,
    created_before: Optional[DateTimeLike] = None,
    include_annotations: bool = True,
    page_size: int = _MAX_PAGE_SIZE,
) -> PaginatedCollection:
    if not isinstance(page_size, int) or not 1 <= page_size <= _MAX_PAGE_SIZE:
        raise ValueError(f"page_size must be between 1 and {_MAX_PAGE_SIZE}")
    after = _to_datetime("created_after", created_after)
    before = _to_datetime("created_before", created_before)
    if after and before and after >= before:
        raise ValueError("created_after must be before created_before")
    where = {
        key: value
        for key, value in {
            "projectId": _to_id("project", project_id),
            "labelId": _to_id("label", label),
            "dataRowId": _to_id("data_row", data_row),
            "createdById": _to_id("created_by", created_by),
            "createdAfter": _iso(after),
            "createdBefore": _iso(before),
        }.items()
        if value is not None
    }
    query = """query GetLabelVersionsPyApi(
        $where: LabelVersionsWhereInput!, $first: Int, $from: String
    ) {
        labelVersions(where: $where, first: $first, after: $from) {
            nodes { %s }
            nextCursor
        }
    }""" % _fields(include_annotations)
    # The input object is a nested dict: PaginatedCollection only types
    # scalars.
    params: Dict[str, Any] = {"where": where, "first": page_size}
    return PaginatedCollection(
        client=client,
        query=query,
        params=params,
        dereferencing=["labelVersions", "nodes"],
        obj_class=lambda _, result: _to_version(result),
        cursor_path=["labelVersions", "nextCursor"],
    )


def get_label_version(
    client: "Client", version_id: str, include_annotations: bool = True
) -> Optional[LabelVersion]:
    query = """query GetLabelVersionPyApi($id: ID!) {
        labelVersion(where: { id: $id }) { %s }
    }""" % _fields(include_annotations)
    result = client.execute(query, {"id": _to_id("version_id", version_id)})
    version = (result or {}).get("labelVersion")
    return _to_version(version) if version else None
