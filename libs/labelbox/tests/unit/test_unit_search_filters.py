from datetime import datetime
from labelbox.schema.search_filters import IntegerValue, RangeOperatorWithSingleValue, DateRange, RangeOperatorWithValue, DateRangeValue, DateValue, IdOperator, OperationType, OrganizationFilter, ProjectStageFilter, TagFilter, TaskCompletedCountFilter, TaskRemainingCountFilter, WorkforceRequestedDateFilter, WorkforceRequestedDateRangeFilter, WorkforceStageUpdatedFilter, WorkforceStageUpdatedRangeFilter, WorkspaceFilter, build_search_filter
from labelbox.utils import format_iso_datetime


def test_id_filters():
    filters = [
        OrganizationFilter(operation=OperationType.Organization,
                           operator=IdOperator.Is,
                           values=["clphb4vd7000cd2wv1ktu5cwa"]),
        WorkspaceFilter(operation=OperationType.Workspace,
                        operator=IdOperator.Is,
                        values=["clphb4vd7000cd2wv1ktu5cwa"]),
        TagFilter(operation=OperationType.Tag,
                  operator=IdOperator.Is,
                  values=["tag"]),
        ProjectStageFilter(operation=OperationType.Stage,
                           operator=IdOperator.Is,
                           values=["requested"]),
    ]

    assert build_search_filter(
        filters
    ) == '[{operator: "is", values: ["clphb4vd7000cd2wv1ktu5cwa"], type: "organization"}, {operator: "is", values: ["clphb4vd7000cd2wv1ktu5cwa"], type: "workspace"}, {operator: "is", values: ["tag"], type: "tag"}, {operator: "is", values: ["requested"], type: "stage"}]'


def test_date_filters():
    local_time_start = datetime.strptime("2024-01-01", "%Y-%m-%d")
    local_time_end = datetime.strptime("2025-01-01", "%Y-%m-%d")

    filters = [
        WorkforceRequestedDateFilter(
            operation=OperationType.WorforceRequestedDate,
            value=DateValue(
                operator=RangeOperatorWithSingleValue.GreaterThanOrEqual,
                value=local_time_start)),
        WorkforceStageUpdatedFilter(
            operation=OperationType.WorkforceStageUpdatedDate,
            value=DateValue(
                operator=RangeOperatorWithSingleValue.LessThanOrEqual,
                value=local_time_end)),
    ]
    expected_start = format_iso_datetime(local_time_start)
    expected_end = format_iso_datetime(local_time_end)

    expected = '[{value: {operator: "GREATER_THAN_OR_EQUAL", value: "' + expected_start + '"}, type: "workforce_requested_at"}, {value: {operator: "LESS_THAN_OR_EQUAL", value: "' + expected_end + '"}, type: "workforce_stage_updated_at"}]'
    assert build_search_filter(filters) == expected


def test_date_range_filters():
    filters = [
        WorkforceRequestedDateRangeFilter(
            operation=OperationType.WorforceRequestedDate,
            value=DateRangeValue(operator=RangeOperatorWithValue.Between,
                                 value=DateRange(min=datetime.strptime(
                                     "2024-01-01T00:00:00-0800",
                                     "%Y-%m-%dT%H:%M:%S%z"),
                                                 max=datetime.strptime(
                                                     "2025-01-01T00:00:00-0800",
                                                     "%Y-%m-%dT%H:%M:%S%z")))),
        WorkforceStageUpdatedRangeFilter(
            operation=OperationType.WorkforceStageUpdatedDate,
            value=DateRangeValue(operator=RangeOperatorWithValue.Between,
                                 value=DateRange(min=datetime.strptime(
                                     "2024-01-01T00:00:00-0800",
                                     "%Y-%m-%dT%H:%M:%S%z"),
                                                 max=datetime.strptime(
                                                     "2025-01-01T00:00:00-0800",
                                                     "%Y-%m-%dT%H:%M:%S%z")))),
    ]
    assert build_search_filter(
        filters
    ) == '[{value: {operator: "BETWEEN", value: {min: "2024-01-01T08:00:00Z", max: "2025-01-01T08:00:00Z"}}, type: "workforce_requested_at"}, {value: {operator: "BETWEEN", value: {min: "2024-01-01T08:00:00Z", max: "2025-01-01T08:00:00Z"}}, type: "workforce_stage_updated_at"}]'


def test_task_count_filters():
    filters = [
        TaskCompletedCountFilter(
            operation=OperationType.TaskCompletedCount,
            value=IntegerValue(
                operator=RangeOperatorWithSingleValue.GreaterThanOrEqual,
                value=1)),
        TaskRemainingCountFilter(
            operation=OperationType.TaskRemainingCount,
            value=IntegerValue(
                operator=RangeOperatorWithSingleValue.LessThanOrEqual,
                value=10)),
    ]

    expected = '[{value: {operator: "GREATER_THAN_OR_EQUAL", value: 1}, type: "task_completed_count"}, {value: {operator: "LESS_THAN_OR_EQUAL", value: 10}, type: "task_remaining_count"}]'
    assert build_search_filter(filters) == expected
