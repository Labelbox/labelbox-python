import datetime
from enum import Enum
from typing import List, Union
from pydantic import PlainSerializer, BaseModel, Field

from typing_extensions import Annotated

from pydantic import BaseModel, Field, field_validator
from labelbox.schema.labeling_service_status import LabelingServiceStatus
from labelbox.utils import format_iso_datetime


class BaseSearchFilter(BaseModel):
    """
    Shared code for all search filters
    """

    class Config:
        use_enum_values = True


class OperationTypeEnum(Enum):
    """
    Supported search entity types
    Each type corresponds to a different filter class
    """

    Organization = "organization_id"
    SharedWithOrganization = "shared_with_organizations"
    Workspace = "workspace"
    Tag = "tag"
    Stage = "stage"
    WorforceRequestedDate = "workforce_requested_at"
    WorkforceStageUpdatedDate = "workforce_stage_updated_at"
    TaskCompletedCount = "task_completed_count"
    TaskRemainingCount = "task_remaining_count"


def convert_enum_to_str(enum_or_str: Union[Enum, str]) -> str:
    if isinstance(enum_or_str, Enum):
        return enum_or_str.value
    return enum_or_str


OperationType = Annotated[
    OperationTypeEnum, PlainSerializer(convert_enum_to_str, return_type=str)
]

IsoDatetimeType = Annotated[
    datetime.datetime, PlainSerializer(format_iso_datetime)
]


class IdOperator(Enum):
    """
    Supported operators for ids like org ids, workspace ids, etc
    """

    Is = "is"


class RangeOperatorWithSingleValue(Enum):
    """
    Supported operators for dates
    """

    Equals = "EQUALS"
    GreaterThanOrEqual = "GREATER_THAN_OR_EQUAL"
    LessThanOrEqual = "LESS_THAN_OR_EQUAL"


class RangeDateTimeOperatorWithSingleValue(Enum):
    """
    Supported operators for dates
    """

    GreaterThanOrEqual = "GREATER_THAN_OR_EQUAL"
    LessThanOrEqual = "LESS_THAN_OR_EQUAL"


class RangeOperatorWithValue(Enum):
    """
    Supported operators for date ranges
    """

    Between = "BETWEEN"


class OrganizationFilter(BaseSearchFilter):
    """
    Filter for organization to which projects belong
    """

    operation: OperationType = Field(
        default=OperationType.Organization, serialization_alias="type"
    )
    operator: IdOperator
    values: List[str]


class SharedWithOrganizationFilter(BaseSearchFilter):
    """
    Find project shared with the organization (i.e. not having this organization as a tenantId)
    """

    operation: OperationType = Field(
        default=OperationType.SharedWithOrganization, serialization_alias="type"
    )
    operator: IdOperator
    values: List[str]


class WorkspaceFilter(BaseSearchFilter):
    """
    Filter for workspace
    """

    operation: OperationType = Field(
        default=OperationType.Workspace, serialization_alias="type"
    )
    operator: IdOperator
    values: List[str]


class TagFilter(BaseSearchFilter):
    """
    Filter for project tags
    values are tag ids
    """

    operation: OperationType = Field(
        default=OperationType.Tag, serialization_alias="type"
    )
    operator: IdOperator
    values: List[str]


class ProjectStageFilter(BaseSearchFilter):
    """
    Filter labelbox service / aka project stages
        Stages are: requested, in_progress, completed etc. as described by LabelingServiceStatus
    """

    operation: OperationType = Field(
        default=OperationType.Stage, serialization_alias="type"
    )
    operator: IdOperator
    values: List[LabelingServiceStatus]

    @field_validator("values", mode="before")
    def validate_values(cls, values):
        disallowed_values = [LabelingServiceStatus.Missing]
        for value in values:
            if value in disallowed_values:
                raise ValueError(
                    f"{value} is not a valid value for ProjectStageFilter"
                )

        return values


class DateValue(BaseSearchFilter):
    """
    Date value for a search filter

    Date formats:
        datetime: an existing datetime object
        str the following formats are accepted: YYYY-MM-DD[T]HH:MM[:SS[.ffffff]][Z or [±]HH[:]MM]
        NOTE
            if a date / datetime string is passed without a timezone, we will assume the time is UTC and convert it to a local timezone
            so for a string '2024-01-01' that is run on a computer in PST, we would convert it to '2024-01-01T08:00:00Z'
            while the same string in EST will get converted to '2024-01-01T05:00:00Z'
    """

    operator: RangeDateTimeOperatorWithSingleValue
    value: IsoDatetimeType


class IntegerValue(BaseSearchFilter):
    operator: RangeOperatorWithSingleValue
    value: int


class WorkforceStageUpdatedFilter(BaseSearchFilter):
    """
    Filter for workforce stage updated date
    """

    operation: OperationType = Field(
        default=OperationType.WorkforceStageUpdatedDate,
        serialization_alias="type",
    )
    value: DateValue


class WorkforceRequestedDateFilter(BaseSearchFilter):
    """
    Filter for workforce requested date
    """

    operation: OperationType = Field(
        default=OperationType.WorforceRequestedDate, serialization_alias="type"
    )
    value: DateValue


class DateRange(BaseSearchFilter):
    """
    Date range for a search filter
    """

    min: IsoDatetimeType
    max: IsoDatetimeType


class DateRangeValue(BaseSearchFilter):
    """
    Date range value for a search filter
    """

    operator: RangeOperatorWithValue
    value: DateRange


class WorkforceRequestedDateRangeFilter(BaseSearchFilter):
    """
    Filter for workforce requested date range
    """

    operation: OperationType = Field(
        default=OperationType.WorforceRequestedDate, serialization_alias="type"
    )
    value: DateRangeValue


class WorkforceStageUpdatedRangeFilter(BaseSearchFilter):
    """
    Filter for workforce stage updated date range
    """

    operation: OperationType = Field(
        default=OperationType.WorkforceStageUpdatedDate,
        serialization_alias="type",
    )
    value: DateRangeValue


class TaskCompletedCountFilter(BaseSearchFilter):
    """
    Filter for completed tasks count
        A task maps to a data row. Task completed should map to a data row in a labeling queue DONE
    """

    operation: OperationType = Field(
        default=OperationType.TaskCompletedCount, serialization_alias="type"
    )
    value: IntegerValue


class TaskRemainingCountFilter(BaseSearchFilter):
    """
    Filter for remaining tasks count. Reverse of TaskCompletedCountFilter
    """

    operation: OperationType = Field(
        default=OperationType.TaskRemainingCount, serialization_alias="type"
    )
    value: IntegerValue


SearchFilter = Union[
    OrganizationFilter,
    WorkspaceFilter,
    SharedWithOrganizationFilter,
    TagFilter,
    ProjectStageFilter,
    WorkforceRequestedDateFilter,
    WorkforceStageUpdatedFilter,
    WorkforceRequestedDateRangeFilter,
    WorkforceStageUpdatedRangeFilter,
    TaskCompletedCountFilter,
    TaskRemainingCountFilter,
]


def _dict_to_graphql_string(d: Union[dict, list, str, int]) -> str:
    if isinstance(d, dict):
        return (
            "{"
            + ", ".join(
                f"{k}: {_dict_to_graphql_string(v)}" for k, v in d.items()
            )
            + "}"
        )
    elif isinstance(d, list):
        return (
            "[" + ", ".join(_dict_to_graphql_string(item) for item in d) + "]"
        )
    else:
        return f'"{d}"' if isinstance(d, str) else str(d)


def build_search_filter(filter: List[SearchFilter]):
    """
    Converts a list of search filters to a graphql string
    """
    filters = [
        _dict_to_graphql_string(f.model_dump(by_alias=True)) for f in filter
    ]
    return "[" + ", ".join(filters) + "]"
