import pytest

from labelbox.schema.queue_mode import QueueMode
import labelbox.exceptions


@pytest.fixture
def project(client, rand_gen):
    # project with no media type
    project = client.create_project(name=rand_gen(str),
                                    queue_mode=QueueMode.Batch,
                                    media_type=None)
    yield project
    project.delete()


@pytest.skip
def test_export_v2_without_media_type(client, export_v2_test_helpers,
                                      wait_for_data_row_processing):
    data_row = wait_for_data_row_processing(client, data_row)
    project.media_type = None

    task_name = "test_label_export_v2_without_media_type"
    params = {
        "include_performance_details": True,
        "include_labels": True,
        "media_type_override": None,
        "project_details": True,
        "data_row_details": True
    }
    with pytest.raises(labelbox.exceptions.LabelboxError):
        export_v2_test_helpers.run_project_export_v2_task(project,
                                                          task_name=task_name,
                                                          params=params)
