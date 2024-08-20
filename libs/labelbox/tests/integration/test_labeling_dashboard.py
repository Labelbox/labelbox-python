from datetime import datetime, timedelta
from labelbox.schema.labeling_service import LabelingServiceStatus
from labelbox.schema.search_filters import DateOperator, DateRange, DateRangeOperator, DateRangeValue, DateValue, IdOperator, OperationType, OrganizationFilter, WorkforceRequestedDateFilter, WorkforceRequestedDateRangeFilter, WorkspaceFilter


def test_request_labeling_service_dashboard(rand_gen,
                                            offline_chat_evaluation_project,
                                            chat_evaluation_ontology,
                                            offline_conversational_data_row):
    project = offline_chat_evaluation_project
    project.connect_ontology(chat_evaluation_ontology)

    project.create_batch(
        rand_gen(str),
        [offline_conversational_data_row.uid],  # sample of data row objects
    )
    labeling_service_dashboard = project.labeling_service_dashboard()
    assert labeling_service_dashboard.status == LabelingServiceStatus.Missing
    assert labeling_service_dashboard.tasks_completed == 0
    assert labeling_service_dashboard.tasks_remaining == 0

    labeling_service_dashboard = [
        ld for ld in project.client.get_labeling_service_dashboards()
    ][0]
    assert labeling_service_dashboard.status == LabelingServiceStatus.Missing
    assert labeling_service_dashboard.tasks_completed == 0
    assert labeling_service_dashboard.tasks_remaining == 0


def test_request_labeling_service_dashboard_filters(requested_labeling_service):
    project, _ = requested_labeling_service

    organization = project.client.get_organization()
    org_filter = OrganizationFilter(operation=OperationType.Organization,
                                    operator=IdOperator.Is,
                                    values=[organization.uid])

    labeling_service_dashboard = [
        ld for ld in project.client.get_labeling_service_dashboards(
            search_query=[org_filter])
    ][0]
    assert labeling_service_dashboard is not None

    workforce_requested_filter_before = WorkforceRequestedDateFilter(
        operation=OperationType.WorforceRequestedDate,
        value=DateValue(operator=DateOperator.GreaterThanOrEqual,
                        value=datetime.strptime("2024-01-01", "%Y-%m-%d")))
    year_from_now = (datetime.now() + timedelta(days=365))
    workforce_requested_filter_after = WorkforceRequestedDateFilter(
        operation=OperationType.WorforceRequestedDate,
        value=DateValue(operator=DateOperator.LessThanOrEqual,
                        value=year_from_now))

    labeling_service_dashboard = [
        ld
        for ld in project.client.get_labeling_service_dashboards(search_query=[
            workforce_requested_filter_after, workforce_requested_filter_before
        ])
    ][0]
    assert labeling_service_dashboard is not None

    workforce_date_range_filter = WorkforceRequestedDateRangeFilter(
        operation=OperationType.WorforceRequestedDate,
        value=DateRangeValue(operator=DateRangeOperator.Between,
                             value=DateRange(min="2024-01-01T00:00:00-0800",
                                             max=year_from_now)))

    labeling_service_dashboard = [
        ld for ld in project.client.get_labeling_service_dashboards(
            search_query=[workforce_date_range_filter])
    ][0]
    assert labeling_service_dashboard is not None

    # with non existing data
    workspace_id = "clzzu4rme000008l42vnl4kre"
    workspace_filter = WorkspaceFilter(operation=OperationType.Workspace,
                                       operator=IdOperator.Is,
                                       values=[workspace_id])
    labeling_service_dashboard = [
        ld for ld in project.client.get_labeling_service_dashboards(
            search_query=[workspace_filter])
    ]
    assert len(labeling_service_dashboard) == 0
    assert labeling_service_dashboard == []
    labeling_service_dashboard = project.client.get_labeling_service_dashboards(
    ).get_one()
    assert labeling_service_dashboard
