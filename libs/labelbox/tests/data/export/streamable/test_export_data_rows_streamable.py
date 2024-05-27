import json
import time

import pytest

from labelbox import DataRow, ExportTask, StreamType


class TestExportDataRow:

    def test_with_data_row_object(self, client, data_row,
                                  wait_for_data_row_processing):
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
        assert export_task.get_total_file_size(
            stream_type=StreamType.RESULT) > 0
        assert export_task.get_total_lines(stream_type=StreamType.RESULT) == 1
        assert (json.loads(list(export_task.get_stream())[0].json_str)
                ["data_row"]["id"] == data_row.uid)
        
    def test_with_data_row_object_buffered(self, client, data_row,
                                  wait_for_data_row_processing):
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
        assert export_task.get_total_file_size(
            stream_type=StreamType.RESULT) > 0
        assert export_task.get_total_lines(stream_type=StreamType.RESULT) == 1
        assert list(export_task.get_buffered_stream())[0].json["data_row"]["id"] == data_row.uid

    def test_with_id(self, client, data_row, wait_for_data_row_processing):
        data_row = wait_for_data_row_processing(client, data_row)
        time.sleep(7)  # temp fix for ES indexing delay
        export_task = DataRow.export(client=client,
                                     data_rows=[data_row.uid],
                                     task_name="TestExportDataRow:test_with_id")
        export_task.wait_till_done()
        assert export_task.status == "COMPLETE"
        assert isinstance(export_task, ExportTask)
        assert export_task.has_result()
        assert export_task.has_errors() is False
        assert export_task.get_total_file_size(
            stream_type=StreamType.RESULT) > 0
        assert export_task.get_total_lines(stream_type=StreamType.RESULT) == 1
        assert (json.loads(list(export_task.get_stream())[0].json_str)
                ["data_row"]["id"] == data_row.uid)

    def test_with_global_key(self, client, data_row,
                             wait_for_data_row_processing):
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
        assert export_task.get_total_file_size(
            stream_type=StreamType.RESULT) > 0
        assert export_task.get_total_lines(stream_type=StreamType.RESULT) == 1
        assert (json.loads(list(export_task.get_stream())[0].json_str)
                ["data_row"]["id"] == data_row.uid)

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
        assert export_task.get_total_file_size(
            stream_type=StreamType.RESULT) is None
        assert export_task.get_total_lines(
            stream_type=StreamType.RESULT) is None
