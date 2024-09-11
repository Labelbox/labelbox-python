from datetime import datetime, timedelta
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
    TaskCompletedCountFilter,
    WorkforceRequestedDateFilter,
    WorkforceRequestedDateRangeFilter,
    WorkspaceFilter,
    TaskRemainingCountFilter,
)


def test_request_labeling_service_dashboard(requested_labeling_service):
    project, _ = requested_labeling_service

    try:
        project.get_labeling_service_dashboard()
    except Exception as e:
        assert False, f"An exception was raised: {e}"

    try:
        project.client.get_labeling_service_dashboards().get_one()
    except Exception as e:
        assert False, f"An exception was raised: {e}"


def test_request_labeling_service_dashboard_filters(requested_labeling_service):
    project, _ = requested_labeling_service

    organization = project.client.get_organization()
    org_filter = OrganizationFilter(
        operator=IdOperator.Is, values=[organization.uid]
    )

    try:
        project.client.get_labeling_service_dashboards(
            search_query=[org_filter]
        ).get_one()
    except Exception as e:
        assert False, f"An exception was raised: {e}"

    workforce_requested_filter_after = WorkforceRequestedDateFilter(
        operation=OperationType.WorforceRequestedDate,
        value=DateValue(
            operator=RangeDateTimeOperatorWithSingleValue.GreaterThanOrEqual,
            value=datetime.strptime("2024-01-01", "%Y-%m-%d"),
        ),
    )
    year_from_now = datetime.now() + timedelta(days=365)
    workforce_requested_filter_before = WorkforceRequestedDateFilter(
        operation=OperationType.WorforceRequestedDate,
        value=DateValue(
            operator=RangeDateTimeOperatorWithSingleValue.LessThanOrEqual,
            value=year_from_now,
        ),
    )

    try:
        project.client.get_labeling_service_dashboards(
            search_query=[
                workforce_requested_filter_after,
                workforce_requested_filter_before,
            ]
        ).get_one()
    except Exception as e:
        assert False, f"An exception was raised: {e}"

    workforce_date_range_filter = WorkforceRequestedDateRangeFilter(
        operation=OperationType.WorforceRequestedDate,
        value=DateRangeValue(
            operator=RangeOperatorWithValue.Between,
            value=DateRange(min="2024-01-01T00:00:00-0800", max=year_from_now),
        ),
    )

    try:
        project.client.get_labeling_service_dashboards(
            search_query=[workforce_date_range_filter]
        ).get_one()
    except Exception as e:
        assert False, f"An exception was raised: {e}"

    # with non existing data
    workspace_id = "clzzu4rme000008l42vnl4kre"
    workspace_filter = WorkspaceFilter(
        operation=OperationType.Workspace,
        operator=IdOperator.Is,
        values=[workspace_id],
    )
    labeling_service_dashboard = [
        ld
        for ld in project.client.get_labeling_service_dashboards(
            search_query=[workspace_filter]
        )
    ]
    assert len(labeling_service_dashboard) == 0
    assert labeling_service_dashboard == []

    task_done_count_filter = TaskCompletedCountFilter(
        operation=OperationType.TaskCompletedCount,
        value=IntegerValue(
            operator=RangeOperatorWithSingleValue.GreaterThanOrEqual, value=0
        ),
    )
    task_remaining_count_filter = TaskRemainingCountFilter(
        operation=OperationType.TaskRemainingCount,
        value=IntegerValue(
            operator=RangeOperatorWithSingleValue.GreaterThanOrEqual, value=0
        ),
    )

    try:
        project.client.get_labeling_service_dashboards(
            search_query=[task_done_count_filter, task_remaining_count_filter]
        ).get_one()
    except Exception as e:
        assert False, f"An exception was raised: {e}"
