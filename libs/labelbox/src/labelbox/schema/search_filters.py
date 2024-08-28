import datetime
from enum import Enum
from typing import List, Literal, Union

from labelbox.pydantic_compat import BaseModel, validator
from labelbox.schema.labeling_service_status import LabelingServiceStatus
from labelbox.utils import format_iso_datetime


class BaseSearchFilter(BaseModel):
    """
    Shared code for all search filters
    """

    class Config:
        use_enum_values = True

    def dict(self, *args, **kwargs):
        res = super().dict(*args, **kwargs)
        if 'operation' in res:
            res['type'] = res.pop('operation')

        # go through all the keys and convert date to string
        for key in res:
            if isinstance(res[key], datetime.datetime):
                res[key] = format_iso_datetime(res[key])
        return res


class OperationType(Enum):
    """
    Supported search entity types
    Each type corresponds to a different filter class
    """
    Organization = 'organization_id'
    SharedWithOrganization = 'shared_with_organizations'
    Workspace = 'workspace'
    Tag = 'tag'
    Stage = 'stage'
    WorforceRequestedDate = 'workforce_requested_at'
    WorkforceStageUpdatedDate = 'workforce_stage_updated_at'
    TaskCompletedCount = 'task_completed_count'
    TaskRemainingCount = 'task_remaining_count'


class IdOperator(Enum):
    """
    Supported operators for ids like org ids, workspace ids, etc
    """
    Is = 'is'


class RangeOperatorWithSingleValue(Enum):
    """
    Supported operators for dates
    """
    Equals = 'EQUALS'
    GreaterThanOrEqual = 'GREATER_THAN_OR_EQUAL'
    LessThanOrEqual = 'LESS_THAN_OR_EQUAL'


class RangeDateTimeOperatorWithSingleValue(Enum):
    """
    Supported operators for dates
    """
    GreaterThanOrEqual = 'GREATER_THAN_OR_EQUAL'
    LessThanOrEqual = 'LESS_THAN_OR_EQUAL'


class RangeOperatorWithValue(Enum):
    """
    Supported operators for date ranges
    """
    Between = 'BETWEEN'


class OrganizationFilter(BaseSearchFilter):
    """
    Filter for organization to which projects belong
    """
    operation: Literal[OperationType.Organization] = OperationType.Organization
    operator: IdOperator
    values: List[str]


class SharedWithOrganizationFilter(BaseSearchFilter):
    """
    Find project shared with the organization (i.e. not having this organization as a tenantId)
    """
    operation: Literal[
        OperationType.
        SharedWithOrganization] = OperationType.SharedWithOrganization
    operator: IdOperator
    values: List[str]


class WorkspaceFilter(BaseSearchFilter):
    """
    Filter for workspace
    """
    operation: Literal[OperationType.Workspace] = OperationType.Workspace
    operator: IdOperator
    values: List[str]


class TagFilter(BaseSearchFilter):
    """
    Filter for project tags
    
    values are tag ids
    """
    operation: Literal[OperationType.Tag] = OperationType.Tag
    operator: IdOperator
    values: List[str]


class ProjectStageFilter(BaseSearchFilter):
    """
    Filter labelbox service / aka project stages
        Stages are: requested, in_progress, completed etc. as described by LabelingServiceStatus
    """
    operation: Literal[OperationType.Stage] = OperationType.Stage
    operator: IdOperator
    values: List[LabelingServiceStatus]

    @validator('values', pre=True)
    def validate_values(cls, values):
        disallowed_values = [LabelingServiceStatus.Missing]
        for value in values:
            if value in disallowed_values:
                raise ValueError(
                    f"{value} is not a valid value for ProjectStageFilter")

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
    value: datetime.datetime


class IntegerValue(BaseSearchFilter):
    operator: RangeOperatorWithSingleValue
    value: int


class WorkforceStageUpdatedFilter(BaseSearchFilter):
    """
    Filter for workforce stage updated date
    """
    operation: Literal[
        OperationType.
        WorkforceStageUpdatedDate] = OperationType.WorkforceStageUpdatedDate
    value: DateValue


class WorkforceRequestedDateFilter(BaseSearchFilter):
    """
    Filter for workforce requested date
    """
    operation: Literal[
        OperationType.
        WorforceRequestedDate] = OperationType.WorforceRequestedDate
    value: DateValue


class DateRange(BaseSearchFilter):
    """
    Date range for a search filter
    """
    min: datetime.datetime
    max: datetime.datetime


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
    operation: Literal[
        OperationType.
        WorforceRequestedDate] = OperationType.WorforceRequestedDate
    value: DateRangeValue


class WorkforceStageUpdatedRangeFilter(BaseSearchFilter):
    """
    Filter for workforce stage updated date range
    """
    operation: Literal[
        OperationType.
        WorkforceStageUpdatedDate] = OperationType.WorkforceStageUpdatedDate
    value: DateRangeValue


class TaskCompletedCountFilter(BaseSearchFilter):
    """
    Filter for completed tasks count
        A task maps to a data row. Task completed should map to a data row in a labeling queue DONE
    """
    operation: Literal[
        OperationType.TaskCompletedCount] = OperationType.TaskCompletedCount
    value: IntegerValue


class TaskRemainingCountFilter(BaseSearchFilter):
    """
    Filter for remaining tasks count. Reverse of TaskCompletedCountFilter
    """
    operation: Literal[
        OperationType.TaskRemainingCount] = OperationType.TaskRemainingCount
    value: IntegerValue


SearchFilter = Union[OrganizationFilter, WorkspaceFilter,
                     SharedWithOrganizationFilter, TagFilter,
                     ProjectStageFilter, WorkforceRequestedDateFilter,
                     WorkforceStageUpdatedFilter,
                     WorkforceRequestedDateRangeFilter,
                     WorkforceStageUpdatedRangeFilter, TaskCompletedCountFilter,
                     TaskRemainingCountFilter]


def _dict_to_graphql_string(d: Union[dict, list, str, int]) -> str:
    if isinstance(d, dict):
        return "{" + ", ".join(
            f'{k}: {_dict_to_graphql_string(v)}' for k, v in d.items()) + "}"
    elif isinstance(d, list):
        return "[" + ", ".join(
            _dict_to_graphql_string(item) for item in d) + "]"
    else:
        return f'"{d}"' if isinstance(d, str) else str(d)


def build_search_filter(filter: List[SearchFilter]):
    """
    Converts a list of search filters to a graphql string
    """
    filters = [_dict_to_graphql_string(f.dict()) for f in filter]
    return "[" + ", ".join(filters) + "]"
