import pytest
import uuid
from typing import Tuple

from labelbox.schema.media_type import MediaType
from labelbox import Project, Dataset
from labelbox.schema.data_row import DataRow
from labelbox.schema.label import Label

IMAGE_URL = "https://storage.googleapis.com/lb-artifacts-testing-public/sdk_integration_test/potato.jpeg"


def test_project_export_v2(client, export_v2_test_helpers,
                           configured_project_with_label,
                           wait_for_data_row_processing):
    project, dataset, data_row, label = configured_project_with_label
    data_row = wait_for_data_row_processing(client, data_row)
    label_id = label.uid

    task_name = "test_label_export_v2"
    params = {
        "include_performance_details": True,
        "include_labels": True,
        "media_type_override": MediaType.Image,
        "project_details": True,
        "data_row_details": True
    }

    task_results = export_v2_test_helpers.run_project_export_v2_task(
        project, task_name=task_name, params=params)

    for task_result in task_results:
        task_media_attributes = task_result['media_attributes']
        task_project = task_result['projects'][project.uid]
        task_project_label_ids_set = set(
            map(lambda prediction: prediction['id'], task_project['labels']))
        task_project_details = task_project['project_details']
        task_data_row = task_result['data_row']
        task_data_row_details = task_data_row['details']

        assert label_id in task_project_label_ids_set
        # data row
        assert task_data_row['id'] == data_row.uid
        assert task_data_row['external_id'] == data_row.external_id
        assert task_data_row['row_data'] == data_row.row_data

        # data row details
        assert task_data_row_details['dataset_id'] == dataset.uid
        assert task_data_row_details['dataset_name'] == dataset.name

        assert task_data_row_details['last_activity_at'] is not None
        assert task_data_row_details['created_by'] is not None

        # media attributes
        assert task_media_attributes['mime_type'] == data_row.media_attributes[
            'mimeType']

        # project name and details
        assert task_project['name'] == project.name
        batch = next(project.batches())
        assert task_project_details['batch_id'] == batch.uid
        assert task_project_details['batch_name'] == batch.name
        assert task_project_details['priority'] is not None
        assert task_project_details[
            'consensus_expected_label_count'] is not None
        assert task_project_details['workflow_history'] is not None

        # label details
        assert task_project['labels'][0]['id'] == label_id


def test_project_export_v2_date_filters(client, export_v2_test_helpers,
                                        configured_project_with_label,
                                        wait_for_data_row_processing):
    project, _, data_row, label = configured_project_with_label
    data_row = wait_for_data_row_processing(client, data_row)
    label_id = label.uid

    task_name = "test_label_export_v2_date_filters"

    filters = {
        "last_activity_at": ["2000-01-01 00:00:00", "2050-01-01 00:00:00"],
        "label_created_at": ["2000-01-01 00:00:00", "2050-01-01 00:00:00"],
        "task_queue_status": "InReview"
    }

    # TODO: Right now we don't have a way to test this
    include_performance_details = True
    params = {
        "performance_details": include_performance_details,
        "include_labels": True,
        "project_details": True,
        "media_type_override": MediaType.Image
    }

    task_queues = project.task_queues()

    review_queue = next(
        tq for tq in task_queues if tq.queue_type == "MANUAL_REVIEW_QUEUE")
    project.move_data_rows_to_task_queue([data_row.uid], review_queue.uid)

    task_results = export_v2_test_helpers.run_project_export_v2_task(
        project, task_name=task_name, filters=filters, params=params)

    for task_result in task_results:
        task_project = task_result['projects'][project.uid]
        task_project_label_ids_set = set(
            map(lambda prediction: prediction['id'], task_project['labels']))
        assert label_id in task_project_label_ids_set
        assert task_project['project_details']['workflow_status'] == 'IN_REVIEW'

        # TODO: Add back in when we have a way to test this
        # if include_performance_details:
        #     assert 'include_performance_details' in task_result and task_result[
        #         'include_performance_details'] is not None
        # else:
        #     assert 'include_performance_details' not in task_result or task_result[
        #         'include_performance_details'] is None

    filters = {"last_activity_at": [None, "2050-01-01 00:00:00"]}
    export_v2_test_helpers.run_project_export_v2_task(project, filters=filters)

    filters = {"label_created_at": ["2000-01-01 00:00:00", None]}
    export_v2_test_helpers.run_project_export_v2_task(project, filters=filters)


def test_project_export_v2_with_iso_date_filters(client, export_v2_test_helpers,
                                                 configured_project_with_label,
                                                 wait_for_data_row_processing):
    project, _, data_row, label = configured_project_with_label
    data_row = wait_for_data_row_processing(client, data_row)
    label_id = label.uid

    task_name = "test_label_export_v2_with_iso_date_filters"

    filters = {
        "last_activity_at": [
            "2000-01-01T00:00:00+0230", "2050-01-01T00:00:00+0230"
        ],
        "label_created_at": [
            "2000-01-01T00:00:00+0230", "2050-01-01T00:00:00+0230"
        ]
    }
    task_results = export_v2_test_helpers.run_project_export_v2_task(
        project, task_name=task_name, filters=filters)
    assert label_id == task_results[0]['projects'][
        project.uid]['labels'][0]['id']

    filters = {"last_activity_at": [None, "2050-01-01T00:00:00+0230"]}
    task_results = export_v2_test_helpers.run_project_export_v2_task(
        project, task_name=task_name, filters=filters)
    assert label_id == task_results[0]['projects'][
        project.uid]['labels'][0]['id']

    filters = {"label_created_at": ["2050-01-01T00:00:00+0230", None]}
    task_results = export_v2_test_helpers.run_project_export_v2_task(
        project, task_name=task_name, filters=filters)
    assert len(task_results) == 0


@pytest.mark.parametrize("data_rows", [3], indirect=True)
def test_project_export_v2_datarows_filter(
        export_v2_test_helpers,
        configured_batch_project_with_multiple_datarows):
    project, _, data_rows = configured_batch_project_with_multiple_datarows

    data_row_ids = [dr.uid for dr in data_rows]
    datarow_filter_size = 2

    filters = {
        "last_activity_at": ["2000-01-01 00:00:00", "2050-01-01 00:00:00"],
        "label_created_at": ["2000-01-01 00:00:00", "2050-01-01 00:00:00"],
        "data_row_ids": data_row_ids[:datarow_filter_size]
    }
    params = {"data_row_details": True, "media_type_override": MediaType.Image}
    task_results = export_v2_test_helpers.run_project_export_v2_task(
        project, filters=filters, params=params)

    # only 2 datarows should be exported
    assert len(task_results) == datarow_filter_size
    # only filtered datarows should be exported
    assert set([dr['data_row']['id'] for dr in task_results
               ]) == set(data_row_ids[:datarow_filter_size])

    global_keys = [dr.global_key for dr in data_rows]
    filters = {
        "last_activity_at": ["2000-01-01 00:00:00", "2050-01-01 00:00:00"],
        "label_created_at": ["2000-01-01 00:00:00", "2050-01-01 00:00:00"],
        "global_keys": global_keys[:datarow_filter_size]
    }
    params = {"data_row_details": True, "media_type_override": MediaType.Image}
    task_results = export_v2_test_helpers.run_project_export_v2_task(
        project, filters=filters, params=params)

    # only 2 datarows should be exported
    assert len(task_results) == datarow_filter_size
    # only filtered datarows should be exported
    assert set([dr['data_row']['global_key'] for dr in task_results
               ]) == set(global_keys[:datarow_filter_size])


def test_batch_project_export_v2(
        configured_batch_project_with_label: Tuple[Project, Dataset, DataRow,
                                                   Label],
        export_v2_test_helpers, dataset: Dataset, image_url: str):
    project, dataset, *_ = configured_batch_project_with_label

    batch = list(project.batches())[0]
    filters = {
        "last_activity_at": ["2000-01-01 00:00:00", "2050-01-01 00:00:00"],
        "label_created_at": ["2000-01-01 00:00:00", "2050-01-01 00:00:00"],
        "batch_ids": [batch.uid],
    }
    params = {
        "include_performance_details": True,
        "include_labels": True,
        "media_type_override": MediaType.Image
    }
    task_name = "test_batch_export_v2"
    task = dataset.create_data_rows([
        {
            "row_data": image_url,
            "external_id": "my-image"
        },
    ] * 2)
    task.wait_till_done()
    data_rows = [dr.uid for dr in list(dataset.export_data_rows())]
    batch_one = f'batch one {uuid.uuid4()}'

    # This test creates two batches, only one batch should be exporter
    # Creatin second batch that will not be used in the export due to the filter: batch_id
    project.create_batch(batch_one, data_rows)

    task_results = export_v2_test_helpers.run_project_export_v2_task(
        project, task_name=task_name, filters=filters, params=params)
    assert (batch.size == len(task_results))
