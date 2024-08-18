import datetime
from enum import Enum
from typing import List, Literal, Union

from labelbox.pydantic_compat import BaseModel, Field


class BaseSearchFilter(BaseModel):

    class Config:
        use_enum_values = True

    def dict(self, *args, **kwargs):
        res = super().dict(*args, **kwargs)
        if 'operation' in res:
            res['type'] = res.pop('operation')

        # go through all the keys and convert date to string
        for key in res:
            if isinstance(res[key], datetime.date):
                res[key] = res[key].isoformat()
        return res


class OperationType(Enum):
    Organization = 'organization'
    Workspace = 'workspace'
    Tag = 'tag'
    Stage = 'stage'
    WorforceRequestedDate = 'workforce_requested_at'
    WorkforceStageUpdatedDate = 'workforce_stage_updated_at'


class IdOperator(Enum):
    Is = 'is'


class DateOperator(Enum):
    Equals = 'EQUALS'
    GreaterThanOrEqual = 'GREATER_THAN_OR_EQUAL'
    LessThanOrEqual = 'LESS_THAN_OR_EQUAL'


class DateRangeOperator(Enum):
    Between = 'BETWEEN'


class OrganizationFilter(BaseSearchFilter):
    operation: Literal[OperationType.Organization]
    operator: IdOperator
    values: List[str]


class WorkspaceFilter(BaseSearchFilter):
    operation: Literal[OperationType.Workspace]
    operator: IdOperator
    values: List[str]


class TagFilter(BaseSearchFilter):
    operation: Literal[OperationType.Tag]
    operator: IdOperator
    values: List[str]


class ProjectStageFilter(BaseSearchFilter):
    operation: Literal[OperationType.Stage]
    operator: IdOperator
    values: List[str]


class DateValue(BaseSearchFilter):
    operator: DateOperator
    value: datetime.date
    # timezone: TimeZoneName = Field(default=TimeZoneName.UTC)  # type: ignore


class WorkforceStageUpdatedFilter(BaseSearchFilter):
    operation: Literal[OperationType.WorkforceStageUpdatedDate]
    value: DateValue


class WorkforceRequestedDateFilter(BaseSearchFilter):
    operation: Literal[OperationType.WorforceRequestedDate]
    value: DateValue


class DateRange(BaseSearchFilter):
    min: datetime.date
    max: datetime.date


class DateRangeValue(BaseSearchFilter):
    operator: DateRangeOperator
    value: DateRange


class WorkforceRequestedDateRangeFilter(BaseSearchFilter):
    operation: Literal[OperationType.WorforceRequestedDate]
    # timezone: TimeZoneName = Field(default=TimeZoneName.UTC)  # type: ignore
    value: DateRangeValue


class WorkforceStageUpdatedRangeFilter(BaseSearchFilter):
    operation: Literal[OperationType.WorkforceStageUpdatedDate]
    # timezone: TimeZoneName = Field(default=TimeZoneName.UTC)  # type: ignore
    value: DateRangeValue


SearchFilter = Union[OrganizationFilter, WorkspaceFilter, TagFilter,
                     ProjectStageFilter, WorkforceRequestedDateFilter,
                     WorkforceStageUpdatedFilter,
                     WorkforceRequestedDateRangeFilter,
                     WorkforceStageUpdatedRangeFilter]


def _dict_to_graphql_string(d: Union[dict, list]) -> str:
    if isinstance(d, dict):
        return "{" + ", ".join(
            f'{k}: {_dict_to_graphql_string(v)}' for k, v in d.items()) + "}"
    elif isinstance(d, list):
        return "[" + ", ".join(
            _dict_to_graphql_string(item) for item in d) + "]"
    else:
        return f'"{d}"' if isinstance(d, str) else str(d)


def build_search_filter(filter: List[SearchFilter]):
    filters = [_dict_to_graphql_string(f.dict()) for f in filter]
    return "[" + ", ".join(filters) + "]"
