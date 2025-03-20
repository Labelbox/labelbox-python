import time

from labelbox import DataRow, ExportTask, StreamType, Task, TaskStatus


class TestExportDataRow:
    def test_with_data_row_object(
        self, client, data_row, wait_for_data_row_processing
    ):
        data_row = wait_for_data_row_processing(client, data_row)
        time.sleep(7)  # temp fix for ES indexing delay
        export_task = DataRow.export(
            client=client,
            data_rows=[data_row],
            task_name="TestExportDataRow:test_with_data_row_object",
        )
        export_task.wait_till_done()
        assert export_task.status == "COMPLETE"
        assert isinstance(export_task, ExportTask)
        assert export_task.has_result()
        assert export_task.has_errors() is False
        assert (
            export_task.get_total_file_size(stream_type=StreamType.RESULT) > 0
        )
        assert export_task.get_total_lines(stream_type=StreamType.RESULT) == 1
        assert (
            list(export_task.get_buffered_stream())[0].json["data_row"]["id"]
            == data_row.uid
        )

    def test_with_data_row_object_buffered(
        self, client, data_row, wait_for_data_row_processing
    ):
        data_row = wait_for_data_row_processing(client, data_row)
        time.sleep(7)  # temp fix for ES indexing delay
        export_task = DataRow.export(
            client=client,
            data_rows=[data_row],
            task_name="TestExportDataRow:test_with_data_row_object_buffered",
        )
        export_task.wait_till_done()
        assert export_task.status == "COMPLETE"
        assert isinstance(export_task, ExportTask)
        assert export_task.has_result()
        assert export_task.has_errors() is False
        assert (
            export_task.get_total_file_size(stream_type=StreamType.RESULT) > 0
        )
        assert export_task.get_total_lines(stream_type=StreamType.RESULT) == 1
        assert (
            list(export_task.get_buffered_stream())[0].json["data_row"]["id"]
            == data_row.uid
        )

    def test_with_id(self, client, data_row, wait_for_data_row_processing):
        data_row = wait_for_data_row_processing(client, data_row)
        time.sleep(7)  # temp fix for ES indexing delay
        export_task = DataRow.export(
            client=client,
            data_rows=[data_row.uid],
            task_name="TestExportDataRow:test_with_id",
        )
        export_task.wait_till_done()
        assert export_task.status == "COMPLETE"
        assert isinstance(export_task, ExportTask)
        assert export_task.has_result()
        assert export_task.has_errors() is False
        assert (
            export_task.get_total_file_size(stream_type=StreamType.RESULT) > 0
        )
        assert export_task.get_total_lines(stream_type=StreamType.RESULT) == 1
        assert (
            list(export_task.get_buffered_stream())[0].json["data_row"]["id"]
            == data_row.uid
        )

    def test_with_global_key(
        self, client, data_row, wait_for_data_row_processing
    ):
        data_row = wait_for_data_row_processing(client, data_row)
        time.sleep(7)  # temp fix for ES indexing delay
        export_task = DataRow.export(
            client=client,
            global_keys=[data_row.global_key],
            task_name="TestExportDataRow:test_with_global_key",
        )
        export_task.wait_till_done()
        assert export_task.status == "COMPLETE"
        assert isinstance(export_task, ExportTask)
        assert export_task.has_result()
        assert export_task.has_errors() is False
        assert (
            export_task.get_total_file_size(stream_type=StreamType.RESULT) > 0
        )
        assert export_task.get_total_lines(stream_type=StreamType.RESULT) == 1
        assert (
            list(export_task.get_buffered_stream())[0].json["data_row"]["id"]
            == data_row.uid
        )

    def test_with_invalid_id(self, client):
        export_task = DataRow.export(
            client=client,
            data_rows=["invalid_id"],
            task_name="TestExportDataRow:test_with_invalid_id",
        )
        export_task.wait_till_done()
        assert export_task.status == "COMPLETE"
        assert isinstance(export_task, ExportTask)
        assert export_task.has_result() is False
        assert export_task.has_errors() is False
        assert (
            export_task.get_total_file_size(stream_type=StreamType.RESULT)
            is None
        )
        assert (
            export_task.get_total_lines(stream_type=StreamType.RESULT) is None
        )

    def test_cancel_export_task(
        self, client, data_row, wait_for_data_row_processing
    ):
        data_row = wait_for_data_row_processing(client, data_row)
        time.sleep(7)  # temp fix for ES indexing delay
        export_task = DataRow.export(
            client=client,
            data_rows=[data_row],
            task_name="TestExportDataRow:test_cancel_export_task",
        )

        # Cancel the task before it completes
        success = client.cancel_task(export_task.uid)
        assert success is True

        # Verify the task was cancelled
        cancelled_task = client.get_task_by_id(export_task.uid)
        assert cancelled_task.status in ["CANCELING", "CANCELED"]

    def test_task_filter(self, client, data_row, wait_for_data_row_processing):
        organization = client.get_organization()
        user = client.get_user()

        export_task = DataRow.export(
            client=client,
            data_rows=[data_row],
            task_name="TestExportDataRow:test_task_filter",
        )

        # Check if task is listed "in progress" in organization's tasks
        org_tasks_in_progress = organization.tasks(
            where=Task.status_as_enum == TaskStatus.In_Progress
        )
        retrieved_task_in_progress = next(
            (t for t in org_tasks_in_progress if t.uid == export_task.uid), ""
        )
        assert getattr(retrieved_task_in_progress, "uid", "") == export_task.uid

        export_task.wait_till_done()

        # Check if task is listed "complete" in user's created tasks
        user_tasks_complete = user.created_tasks(
            where=Task.status_as_enum == TaskStatus.Complete
        )
        retrieved_task_complete = next(
            (t for t in user_tasks_complete if t.uid == export_task.uid), ""
        )
        assert getattr(retrieved_task_complete, "uid", "") == export_task.uid
