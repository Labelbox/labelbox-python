import pytest

from labelbox.exceptions import LabelboxError, OperationNotAllowedException


def test_live_chat_evaluation_project(
        live_chat_evaluation_project_with_new_dataset, model_config):

    project = live_chat_evaluation_project_with_new_dataset

    project.set_project_model_setup_complete()
    assert bool(project.model_setup_complete) is True

    with pytest.raises(
            expected_exception=LabelboxError,
            match=
            "Cannot create model config for project because model setup is complete"
    ):
        project.add_model_config(model_config.uid)


def test_offline_chat_evaluation_project(offline_chat_evaluation_project,
                                         model_config):

    project = offline_chat_evaluation_project

    with pytest.raises(
            expected_exception=OperationNotAllowedException,
            match=
            "Only live model chat evaluation projects can complete model setup"
    ):
        project.set_project_model_setup_complete()


def test_any_other_project(project, model_config):
    with pytest.raises(
            expected_exception=OperationNotAllowedException,
            match=
            "Only live model chat evaluation projects can complete model setup"
    ):
        project.set_project_model_setup_complete()
