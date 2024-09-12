import json

import pytest

from labelbox import ExportTask, StreamType


class TestExportDataset:
    @pytest.mark.parametrize("data_rows", [3], indirect=True)
    def test_export(self, dataset, data_rows):
        expected_data_row_ids = [dr.uid for dr in data_rows]

        export_task = dataset.export(task_name="TestExportDataset:test_export")
        export_task.wait_till_done()

        assert export_task.status == "COMPLETE"
        assert isinstance(export_task, ExportTask)
        assert export_task.has_result()
        assert export_task.has_errors() is False
        assert (
            export_task.get_total_file_size(stream_type=StreamType.RESULT) > 0
        )
        assert export_task.get_total_lines(
            stream_type=StreamType.RESULT
        ) == len(expected_data_row_ids)
        data_row_ids = list(
            map(
                lambda x: json.loads(x.json_str)["data_row"]["id"],
                export_task.get_stream(),
            )
        )
        assert data_row_ids.sort() == expected_data_row_ids.sort()

    @pytest.mark.parametrize("data_rows", [3], indirect=True)
    def test_with_data_row_filter(self, dataset, data_rows):
        datarow_filter_size = 3
        expected_data_row_ids = [dr.uid for dr in data_rows][
            :datarow_filter_size
        ]
        filters = {"data_row_ids": expected_data_row_ids}

        export_task = dataset.export(
            filters=filters,
            task_name="TestExportDataset:test_with_data_row_filter",
        )
        export_task.wait_till_done()

        assert export_task.status == "COMPLETE"
        assert isinstance(export_task, ExportTask)
        assert export_task.has_result()
        assert export_task.has_errors() is False
        assert (
            export_task.get_total_file_size(stream_type=StreamType.RESULT) > 0
        )
        assert (
            export_task.get_total_lines(stream_type=StreamType.RESULT)
            == datarow_filter_size
        )
        data_row_ids = list(
            map(
                lambda x: json.loads(x.json_str)["data_row"]["id"],
                export_task.get_stream(),
            )
        )
        assert data_row_ids.sort() == expected_data_row_ids.sort()

    @pytest.mark.parametrize("data_rows", [3], indirect=True)
    def test_with_global_key_filter(self, dataset, data_rows):
        datarow_filter_size = 2
        expected_global_keys = [dr.global_key for dr in data_rows][
            :datarow_filter_size
        ]
        filters = {"global_keys": expected_global_keys}

        export_task = dataset.export(
            filters=filters,
            task_name="TestExportDataset:test_with_global_key_filter",
        )
        export_task.wait_till_done()

        assert export_task.status == "COMPLETE"
        assert isinstance(export_task, ExportTask)
        assert export_task.has_result()
        assert export_task.has_errors() is False
        assert (
            export_task.get_total_file_size(stream_type=StreamType.RESULT) > 0
        )
        assert (
            export_task.get_total_lines(stream_type=StreamType.RESULT)
            == datarow_filter_size
        )
        global_keys = list(
            map(
                lambda x: json.loads(x.json_str)["data_row"]["global_key"],
                export_task.get_stream(),
            )
        )
        assert global_keys.sort() == expected_global_keys.sort()
