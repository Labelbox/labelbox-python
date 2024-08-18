from datetime import date, datetime
from labelbox.schema.search_filters import DateOperator, DateRange, DateRangeOperator, DateRangeValue, DateValue, IdOperator, OperationType, OrganizationFilter, ProjectStageFilter, TagFilter, WorkforceRequestedDateFilter, WorkforceRequestedDateRangeFilter, WorkforceStageUpdatedFilter, WorkforceStageUpdatedRangeFilter, WorkspaceFilter, build_search_filter


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
    filters = [
        WorkforceRequestedDateFilter(
            operation=OperationType.WorforceRequestedDate,
            value=DateValue(operator=DateOperator.GreaterThanOrEqual,
                            value=datetime.strptime("2024-01-01", "%Y-%m-%d"))),
        WorkforceStageUpdatedFilter(
            operation=OperationType.WorkforceStageUpdatedDate,
            value=DateValue(operator=DateOperator.LessThanOrEqual,
                            value=datetime.strptime("2025-01-01", "%Y-%m-%d"))),
    ]
    assert build_search_filter(
        filters
    ) == '[{value: {operator: "GREATER_THAN_OR_EQUAL", value: "2024-01-01T08:00:00Z"}, type: "workforce_requested_at"}, {value: {operator: "LESS_THAN_OR_EQUAL", value: "2025-01-01T08:00:00Z"}, type: "workforce_stage_updated_at"}]'


def test_date_range_filters():
    filters = [
        WorkforceRequestedDateRangeFilter(
            operation=OperationType.WorforceRequestedDate,
            value=DateRangeValue(
                operator=DateRangeOperator.Between,
                value=DateRange(min=datetime.strptime("2024-01-01", "%Y-%m-%d"),
                                max=datetime.strptime("2025-01-01",
                                                      "%Y-%m-%d")))),
        WorkforceStageUpdatedRangeFilter(
            operation=OperationType.WorkforceStageUpdatedDate,
            value=DateRangeValue(operator=DateRangeOperator.Between,
                                 value=DateRange(min="2024-01-01T08:00:00Z",
                                                 max="2025-01-01T08:00:00Z")))
    ]
    assert build_search_filter(
        filters
    ) == '[{value: {operator: "BETWEEN", value: {min: "2024-01-01T08:00:00Z", max: "2025-01-01T08:00:00Z"}}, type: "workforce_requested_at"}, {value: {operator: "BETWEEN", value: {min: "2024-01-01T08:00:00Z", max: "2025-01-01T08:00:00Z"}}, type: "workforce_stage_updated_at"}]'
