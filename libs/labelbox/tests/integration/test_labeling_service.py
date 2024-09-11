import pytest

from labelbox.exceptions import LabelboxError, ResourceNotFoundError
from labelbox.schema.labeling_service import LabelingServiceStatus


def test_start_labeling_service(project):
    # Check that the labeling service is now available
    labeling_service = project.get_labeling_service()  # creates and gets it
    assert labeling_service.status == LabelingServiceStatus.SetUp
    assert labeling_service.project_id == project.uid

    labeling_service_status = project.get_labeling_service_status()
    assert labeling_service_status == LabelingServiceStatus.SetUp


def test_request_labeling_service_moe_offline_project(
    rand_gen,
    offline_chat_evaluation_project,
    chat_evaluation_ontology,
    offline_conversational_data_row,
    model_config,
):
    project = offline_chat_evaluation_project
    project.connect_ontology(chat_evaluation_ontology)

    project.create_batch(
        rand_gen(str),
        [offline_conversational_data_row.uid],  # sample of data row objects
    )

    project.upsert_instructions("tests/integration/media/sample_pdf.pdf")

    labeling_service = project.get_labeling_service()
    labeling_service.request()
    assert (
        project.get_labeling_service_status() == LabelingServiceStatus.Requested
    )


def test_request_labeling_service_moe_project(
    rand_gen,
    live_chat_evaluation_project_with_new_dataset,
    chat_evaluation_ontology,
    model_config,
):
    project = live_chat_evaluation_project_with_new_dataset
    project.connect_ontology(chat_evaluation_ontology)

    project.upsert_instructions("tests/integration/media/sample_pdf.pdf")

    labeling_service = project.get_labeling_service()
    with pytest.raises(
        LabelboxError,
        match='[{"errorType":"PROJECT_MODEL_CONFIG","errorMessage":"Project model config is not completed"}]',
    ):
        labeling_service.request()
    project.add_model_config(model_config.uid)
    project.set_project_model_setup_complete()

    labeling_service.request()
    assert (
        project.get_labeling_service_status() == LabelingServiceStatus.Requested
    )


def test_request_labeling_service_incomplete_requirements(ontology, project):
    labeling_service = (
        project.get_labeling_service()
    )  # project fixture is an Image type project
    with pytest.raises(
        ResourceNotFoundError, match="Associated ontology id could not be found"
    ):  # No labeling service by default
        labeling_service.request()
    project.connect_ontology(ontology)
    with pytest.raises(LabelboxError):
        labeling_service.request()
