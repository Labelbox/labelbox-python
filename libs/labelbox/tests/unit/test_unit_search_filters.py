from datetime import datetime
from labelbox.schema.labeling_service import LabelingServiceStatus
from labelbox.schema.search_filters import (
    IntegerValue,
    RangeDateTimeOperatorWithSingleValue,
    RangeOperatorWithSingleValue,
    DateRange,
    RangeOperatorWithValue,
    DateRangeValue,
    DateValue,
    IdOperator,
    OperationType,
    OrganizationFilter,
    ProjectStageFilter,
    SharedWithOrganizationFilter,
    TagFilter,
    TaskCompletedCountFilter,
    TaskRemainingCountFilter,
    WorkforceRequestedDateFilter,
    WorkforceRequestedDateRangeFilter,
    WorkforceStageUpdatedFilter,
    WorkforceStageUpdatedRangeFilter,
    WorkspaceFilter,
    build_search_filter,
)
from labelbox.utils import format_iso_datetime
import pytest


def test_id_filters():
    filters = [
        OrganizationFilter(
            operator=IdOperator.Is, values=["clphb4vd7000cd2wv1ktu5cwa"]
        ),
        SharedWithOrganizationFilter(
            operator=IdOperator.Is, values=["clphb4vd7000cd2wv1ktu5cwa"]
        ),
        WorkspaceFilter(
            operator=IdOperator.Is, values=["clphb4vd7000cd2wv1ktu5cwa"]
        ),
        TagFilter(operator=IdOperator.Is, values=["cls1vkrw401ab072vg2pq3t5d"]),
        ProjectStageFilter(
            operator=IdOperator.Is, values=[LabelingServiceStatus.Requested]
        ),
    ]

    assert (
        build_search_filter(filters)
        == '[{type: "organization_id", operator: "is", values: ["clphb4vd7000cd2wv1ktu5cwa"]}, {type: "shared_with_organizations", operator: "is", values: ["clphb4vd7000cd2wv1ktu5cwa"]}, {type: "workspace", operator: "is", values: ["clphb4vd7000cd2wv1ktu5cwa"]}, {type: "tag", operator: "is", values: ["cls1vkrw401ab072vg2pq3t5d"]}, {type: "stage", operator: "is", values: ["REQUESTED"]}]'
    )


def test_stage_filter_with_invalid_values():
    with pytest.raises(
        ValueError, match="is not a valid value for ProjectStageFilter"
    ) as e:
        _ = (
            ProjectStageFilter(
                operator=IdOperator.Is,
                values=[
                    LabelingServiceStatus.Requested,
                    LabelingServiceStatus.Missing,
                ],
            ),
        )


def test_date_filters():
    local_time_start = datetime.strptime("2024-01-01", "%Y-%m-%d")
    local_time_end = datetime.strptime("2025-01-01", "%Y-%m-%d")

    filters = [
        WorkforceRequestedDateFilter(
            value=DateValue(
                operator=RangeDateTimeOperatorWithSingleValue.GreaterThanOrEqual,
                value=local_time_start,
            )
        ),
        WorkforceStageUpdatedFilter(
            value=DateValue(
                operator=RangeDateTimeOperatorWithSingleValue.LessThanOrEqual,
                value=local_time_end,
            )
        ),
    ]
    expected_start = format_iso_datetime(local_time_start)
    expected_end = format_iso_datetime(local_time_end)

    expected = (
        '[{type: "workforce_requested_at", value: {operator: "GREATER_THAN_OR_EQUAL", value: "'
        + expected_start
        + '"}}, {type: "workforce_stage_updated_at", value: {operator: "LESS_THAN_OR_EQUAL", value: "'
        + expected_end
        + '"}}]'
    )
    assert build_search_filter(filters) == expected


def test_date_range_filters():
    filters = [
        WorkforceRequestedDateRangeFilter(
            value=DateRangeValue(
                operator=RangeOperatorWithValue.Between,
                value=DateRange(
                    min=datetime.strptime(
                        "2024-01-01T00:00:00-0800", "%Y-%m-%dT%H:%M:%S%z"
                    ),
                    max=datetime.strptime(
                        "2025-01-01T00:00:00-0800", "%Y-%m-%dT%H:%M:%S%z"
                    ),
                ),
            )
        ),
        WorkforceStageUpdatedRangeFilter(
            value=DateRangeValue(
                operator=RangeOperatorWithValue.Between,
                value=DateRange(
                    min=datetime.strptime(
                        "2024-01-01T00:00:00-0800", "%Y-%m-%dT%H:%M:%S%z"
                    ),
                    max=datetime.strptime(
                        "2025-01-01T00:00:00-0800", "%Y-%m-%dT%H:%M:%S%z"
                    ),
                ),
            )
        ),
    ]
    assert (
        build_search_filter(filters)
        == '[{type: "workforce_requested_at", value: {operator: "BETWEEN", value: {min: "2024-01-01T08:00:00Z", max: "2025-01-01T08:00:00Z"}}}, {type: "workforce_stage_updated_at", value: {operator: "BETWEEN", value: {min: "2024-01-01T08:00:00Z", max: "2025-01-01T08:00:00Z"}}}]'
    )


def test_task_count_filters():
    filters = [
        TaskCompletedCountFilter(
            value=IntegerValue(
                operator=RangeOperatorWithSingleValue.GreaterThanOrEqual,
                value=1,
            )
        ),
        TaskRemainingCountFilter(
            value=IntegerValue(
                operator=RangeOperatorWithSingleValue.LessThanOrEqual, value=10
            )
        ),
    ]

    expected = '[{type: "task_completed_count", value: {operator: "GREATER_THAN_OR_EQUAL", value: 1}}, {type: "task_remaining_count", value: {operator: "LESS_THAN_OR_EQUAL", value: 10}}]'
    assert build_search_filter(filters) == expected
