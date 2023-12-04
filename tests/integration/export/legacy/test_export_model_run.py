import time


def _model_run_export_v2_results(model_run, task_name, params, num_retries=5):
    """Export model run results and retry if no results are returned."""
    while (num_retries > 0):
        task = model_run.export_v2(task_name, params=params)
        assert task.name == task_name
        task.wait_till_done()
        assert task.status == "COMPLETE"
        assert task.errors is None
        task_results = task.result
        if len(task_results) == 0:
            num_retries -= 1
            time.sleep(5)
        else:
            return task_results
    return []


def test_model_run_export_v2(model_run_with_data_rows):
    model_run, labels = model_run_with_data_rows
    label_ids = [label.uid for label in labels]
    expected_data_rows = list(model_run.model_run_data_rows())

    task_name = "test_task"
    params = {"media_attributes": True, "predictions": True}
    task_results = _model_run_export_v2_results(model_run, task_name, params)
    assert len(task_results) == len(expected_data_rows)

    for task_result in task_results:
        # Check export param handling
        assert 'media_attributes' in task_result and task_result[
            'media_attributes'] is not None
        exported_model_run = task_result['experiments'][
            model_run.model_id]['runs'][model_run.uid]
        task_label_ids_set = set(
            map(lambda label: label['id'], exported_model_run['labels']))
        task_prediction_ids_set = set(
            map(lambda prediction: prediction['id'],
                exported_model_run['predictions']))
        for label_id in task_label_ids_set:
            assert label_id in label_ids
        for prediction_id in task_prediction_ids_set:
            assert prediction_id in label_ids
