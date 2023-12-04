import json
import time

from labelbox import ExportTask, StreamType


class TestExportModelRun:

    def test_export(self, model_run_with_data_rows):
        model_run, labels = model_run_with_data_rows
        label_ids = [label.uid for label in labels]
        expected_data_rows = list(model_run.model_run_data_rows())

        task_name = "TestExportModelRun:test_export"
        params = {"media_attributes": True, "predictions": True}
        export_task = model_run.export(task_name, params=params)
        assert export_task.name == task_name
        export_task.wait_till_done()

        assert export_task.status == "COMPLETE"
        assert isinstance(export_task, ExportTask)
        assert export_task.has_result()
        assert export_task.has_errors() is False
        assert export_task.get_total_file_size(
            stream_type=StreamType.RESULT) > 0
        assert export_task.get_total_lines(
            stream_type=StreamType.RESULT) == len(expected_data_rows)

        for data in export_task.get_stream():
            obj = json.loads(data.json_str)
            assert "media_attributes" in obj and obj[
                "media_attributes"] is not None
            exported_model_run = obj["experiments"][model_run.model_id]["runs"][
                model_run.uid]
            task_label_ids_set = set(
                map(lambda label: label["id"], exported_model_run["labels"]))
            task_prediction_ids_set = set(
                map(lambda prediction: prediction["id"],
                    exported_model_run["predictions"]))
            for label_id in task_label_ids_set:
                assert label_id in label_ids
            for prediction_id in task_prediction_ids_set:
                assert prediction_id in label_ids
