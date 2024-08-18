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

    assert build_search_filter(filters) == [{
        "operator": "is",
        "values": ["clphb4vd7000cd2wv1ktu5cwa"],
        "type": "organization"
    }, {
        "operator": "is",
        "values": ["clphb4vd7000cd2wv1ktu5cwa"],
        "type": "workspace"
    }, {
        "operator": "is",
        "values": ["tag"],
        "type": "tag"
    }, {
        "operator": "is",
        "values": ["requested"],
        "type": "stage"
    }]


def test_date_filters():
    filters = [
        WorkforceRequestedDateFilter(
            operation=OperationType.WorforceRequestedDate,
            value=DateValue(operator=DateOperator.GreaterThanOrEqual,
                            value="2024-01-01")),
        WorkforceStageUpdatedFilter(
            operation=OperationType.WorkforceStageUpdatedDate,
            value=DateValue(operator=DateOperator.LessThanOrEqual,
                            value="2025-01-01")),
    ]
    assert build_search_filter(filters) == [{
        "type": "workforce_requested_at",
        "value": {
            "operator": "GREATER_THAN_OR_EQUAL",
            "value": "2024-01-01",
        }
    }, {
        "type": "workforce_stage_updated_at",
        "value": {
            "operator": "LESS_THAN_OR_EQUAL",
            "value": "2025-01-01",
        }
    }]


def test_date_range_filters():
    filters = [
        WorkforceRequestedDateRangeFilter(
            operation=OperationType.WorforceRequestedDate,
            value=DateRangeValue(operator=DateRangeOperator.Between,
                                 value=DateRange(min="2024-01-01",
                                                 max="2025-01-01"))),
        WorkforceStageUpdatedRangeFilter(
            operation=OperationType.WorkforceStageUpdatedDate,
            value=DateRangeValue(operator=DateRangeOperator.Between,
                                 value=DateRange(min="2024-01-01",
                                                 max="2025-01-01")))
    ]
    assert build_search_filter(filters) == [{
        "value": {
            "operator": "BETWEEN",
            "value": {
                "min": "2024-01-01",
                "max": "2025-01-01"
            }
        },
        "type": "workforce_requested_at"
    }, {
        "value": {
            "operator": "BETWEEN",
            "value": {
                "min": "2024-01-01",
                "max": "2025-01-01"
            }
        },
        "type": "workforce_stage_updated_at"
    }]
