import json

import pytest
import uuid
from typing import Tuple
from labelbox.schema.export_task import ExportTask, StreamType

from labelbox.schema.media_type import MediaType
from labelbox import Project, Dataset
from labelbox.schema.data_row import DataRow
from labelbox.schema.label import Label

IMAGE_URL = (
    "https://storage.googleapis.com/lb-artifacts-testing-public/sdk_integration_test/potato.jpeg"
)


class TestExportProject:

    @pytest.fixture
    def project_export(self):

        def _project_export(project, task_name, filters=None, params=None):
            export_task = project.export(
                task_name=task_name,
                filters=filters,
                params=params,
            )
            export_task.wait_till_done()

            assert export_task.status == "COMPLETE"
            assert isinstance(export_task, ExportTask)
            return export_task

        return _project_export

    def test_export(
        self,
        client,
        configured_project_with_label,
        wait_for_data_row_processing,
        project_export,
    ):
        project, dataset, data_row, label = configured_project_with_label
        data_row = wait_for_data_row_processing(client, data_row)
        label_id = label.uid
        task_name = "TestExportProject:test_export"
        params = {
            "include_performance_details": True,
            "include_labels": True,
            "media_type_override": MediaType.Image,
            "project_details": True,
            "data_row_details": True,
        }
        export_task = project_export(project, task_name, params=params)
        assert export_task.has_result()
        assert export_task.has_errors() is False
        assert export_task.get_total_file_size(
            stream_type=StreamType.RESULT) > 0
        assert export_task.get_total_lines(stream_type=StreamType.RESULT) > 0

        for data in export_task.get_stream():
            obj = json.loads(data.json_str)
            task_media_attributes = obj["media_attributes"]
            task_project = obj["projects"][project.uid]
            task_project_label_ids_set = set(
                map(lambda prediction: prediction["id"],
                    task_project["labels"]))
            task_project_details = task_project["project_details"]
            task_data_row = obj["data_row"]
            task_data_row_details = task_data_row["details"]

            assert label_id in task_project_label_ids_set
            # data row
            assert task_data_row["id"] == data_row.uid
            assert task_data_row["external_id"] == data_row.external_id
            assert task_data_row["row_data"] == data_row.row_data

            # data row details
            assert task_data_row_details["dataset_id"] == dataset.uid
            assert task_data_row_details["dataset_name"] == dataset.name

            assert task_data_row_details["last_activity_at"] is not None
            assert task_data_row_details["created_by"] is not None

            # media attributes
            assert task_media_attributes[
                "mime_type"] == data_row.media_attributes["mimeType"]

            # project name and details
            assert task_project["name"] == project.name
            batch = next(project.batches())
            assert task_project_details["batch_id"] == batch.uid
            assert task_project_details["batch_name"] == batch.name
            assert task_project_details["priority"] is not None
            assert task_project_details[
                "consensus_expected_label_count"] is not None
            assert task_project_details["workflow_history"] is not None

            # label details
            assert task_project["labels"][0]["id"] == label_id

    def test_with_date_filters(
        self,
        client,
        configured_project_with_label,
        wait_for_data_row_processing,
        project_export,
    ):
        project, _, data_row, label = configured_project_with_label
        data_row = wait_for_data_row_processing(client, data_row)
        label_id = label.uid
        task_name = "TestExportProject:test_with_date_filters"
        filters = {
            "last_activity_at": ["2000-01-01 00:00:00", "2050-01-01 00:00:00"],
            "label_created_at": ["2000-01-01 00:00:00", "2050-01-01 00:00:00"],
            "task_queue_status": "InReview",
        }
        include_performance_details = True
        params = {
            "performance_details": include_performance_details,
            "include_labels": True,
            "project_details": True,
            "media_type_override": MediaType.Image,
        }
        task_queues = project.task_queues()
        review_queue = next(
            tq for tq in task_queues if tq.queue_type == "MANUAL_REVIEW_QUEUE")
        project.move_data_rows_to_task_queue([data_row.uid], review_queue.uid)
        export_task = project_export(project,
                                     task_name,
                                     filters=filters,
                                     params=params)
        assert export_task.has_result()
        assert export_task.has_errors() is False
        assert export_task.get_total_file_size(
            stream_type=StreamType.RESULT) > 0
        assert export_task.get_total_lines(stream_type=StreamType.RESULT) > 0

        for data in export_task.get_stream():
            obj = json.loads(data.json_str)
            task_project = obj["projects"][project.uid]
            task_project_label_ids_set = set(
                map(lambda prediction: prediction["id"],
                    task_project["labels"]))
            assert label_id in task_project_label_ids_set
            assert task_project["project_details"][
                "workflow_status"] == "IN_REVIEW"

    def test_with_iso_date_filters(
        self,
        client,
        configured_project_with_label,
        wait_for_data_row_processing,
        project_export,
    ):
        project, _, data_row, label = configured_project_with_label
        data_row = wait_for_data_row_processing(client, data_row)
        label_id = label.uid
        task_name = "TestExportProject:test_with_iso_date_filters"
        filters = {
            "last_activity_at": [
                "2000-01-01T00:00:00+0230", "2050-01-01T00:00:00+0230"
            ],
            "label_created_at": [
                "2000-01-01T00:00:00+0230", "2050-01-01T00:00:00+0230"
            ],
        }
        export_task = project_export(project, task_name, filters=filters)
        assert export_task.has_result()
        assert export_task.has_errors() is False
        assert export_task.get_total_file_size(
            stream_type=StreamType.RESULT) > 0
        assert export_task.get_total_lines(stream_type=StreamType.RESULT) > 0
        assert (label_id == json.loads(
            list(export_task.get_stream())[0].json_str)["projects"][project.uid]
                ["labels"][0]["id"])

    def test_with_iso_date_filters_no_start_date(
        self,
        client,
        configured_project_with_label,
        wait_for_data_row_processing,
        project_export,
    ):
        project, _, data_row, label = configured_project_with_label
        data_row = wait_for_data_row_processing(client, data_row)
        label_id = label.uid
        task_name = "TestExportProject:test_with_iso_date_filters_no_start_date"
        filters = {"last_activity_at": [None, "2050-01-01T00:00:00+0230"]}
        export_task = project_export(project, task_name, filters=filters)
        assert export_task.has_result()
        assert export_task.has_errors() is False
        assert export_task.get_total_file_size(
            stream_type=StreamType.RESULT) > 0
        assert export_task.get_total_lines(stream_type=StreamType.RESULT) > 0
        assert (label_id == json.loads(
            list(export_task.get_stream())[0].json_str)["projects"][project.uid]
                ["labels"][0]["id"])

    def test_with_iso_date_filters_and_future_start_date(
        self,
        client,
        configured_project_with_label,
        wait_for_data_row_processing,
        project_export,
    ):
        project, _, data_row, _label = configured_project_with_label
        data_row = wait_for_data_row_processing(client, data_row)
        task_name = "TestExportProject:test_with_iso_date_filters_and_future_start_date"
        filters = {"label_created_at": ["2050-01-01T00:00:00+0230", None]}
        export_task = project_export(project, task_name, filters=filters)
        assert export_task.has_result() is False
        assert export_task.has_errors() is False
        assert export_task.get_total_file_size(
            stream_type=StreamType.RESULT) is None
        assert export_task.get_total_lines(
            stream_type=StreamType.RESULT) is None

    @pytest.mark.parametrize("data_rows", [3], indirect=True)
    def test_with_data_row_filter(
            self, configured_batch_project_with_multiple_datarows,
            project_export):
        project, _, data_rows = configured_batch_project_with_multiple_datarows
        datarow_filter_size = 2
        expected_data_row_ids = [dr.uid for dr in data_rows
                                ][:datarow_filter_size]
        task_name = "TestExportProject:test_with_data_row_filter"
        filters = {
            "last_activity_at": ["2000-01-01 00:00:00", "2050-01-01 00:00:00"],
            "label_created_at": ["2000-01-01 00:00:00", "2050-01-01 00:00:00"],
            "data_row_ids": expected_data_row_ids,
        }
        params = {
            "data_row_details": True,
            "media_type_override": MediaType.Image
        }
        export_task = project_export(project,
                                     task_name,
                                     filters=filters,
                                     params=params)
        assert export_task.has_result()
        assert export_task.has_errors() is False
        assert export_task.get_total_file_size(
            stream_type=StreamType.RESULT) > 0
        # only 2 datarows should be exported
        assert export_task.get_total_lines(
            stream_type=StreamType.RESULT) == datarow_filter_size
        data_row_ids = list(
            map(lambda x: json.loads(x.json_str)["data_row"]["id"],
                export_task.get_stream()))
        assert data_row_ids.sort() == expected_data_row_ids.sort()

    @pytest.mark.parametrize("data_rows", [3], indirect=True)
    def test_with_global_key_filter(
            self, configured_batch_project_with_multiple_datarows,
            project_export):
        project, _, data_rows = configured_batch_project_with_multiple_datarows
        datarow_filter_size = 2
        expected_global_keys = [dr.global_key for dr in data_rows
                               ][:datarow_filter_size]
        task_name = "TestExportProject:test_with_global_key_filter"
        filters = {
            "last_activity_at": ["2000-01-01 00:00:00", "2050-01-01 00:00:00"],
            "label_created_at": ["2000-01-01 00:00:00", "2050-01-01 00:00:00"],
            "global_keys": expected_global_keys,
        }
        params = {
            "data_row_details": True,
            "media_type_override": MediaType.Image
        }
        export_task = project_export(project,
                                     task_name,
                                     filters=filters,
                                     params=params)
        assert export_task.has_result()
        assert export_task.has_errors() is False
        assert export_task.get_total_file_size(
            stream_type=StreamType.RESULT) > 0
        # only 2 datarows should be exported
        assert export_task.get_total_lines(
            stream_type=StreamType.RESULT) == datarow_filter_size
        global_keys = list(
            map(lambda x: json.loads(x.json_str)["data_row"]["global_key"],
                export_task.get_stream()))
        assert global_keys.sort() == expected_global_keys.sort()

    def test_batch(
        self,
        configured_batch_project_with_label: Tuple[Project, Dataset, DataRow,
                                                   Label],
        dataset: Dataset,
        image_url: str,
        project_export,
    ):
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
            "media_type_override": MediaType.Image,
        }
        task_name = "TestExportProject:test_batch"
        task = dataset.create_data_rows([
            {
                "row_data": image_url,
                "external_id": "my-image"
            },
        ] * 2)
        task.wait_till_done()
        data_rows = [result["id"] for result in task.result]
        batch_one = f"batch one {uuid.uuid4()}"

        # This test creates two batches, only one batch should be exporter
        # Creatin second batch that will not be used in the export due to the filter: batch_id
        project.create_batch(batch_one, data_rows)

        export_task = project_export(project,
                                     task_name,
                                     filters=filters,
                                     params=params)
        assert export_task.has_result()
        assert export_task.has_errors() is False
        assert export_task.get_total_file_size(
            stream_type=StreamType.RESULT) > 0
        assert export_task.get_total_lines(
            stream_type=StreamType.RESULT) == batch.size
