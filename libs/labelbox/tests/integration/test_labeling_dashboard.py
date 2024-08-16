from labelbox.schema.labeling_service import LabelingServiceStatus


def test_request_labeling_service_moe_offline_project(
        rand_gen, offline_chat_evaluation_project, chat_evaluation_ontology,
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
