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


def test_model_run_export_v2(model_run_with_data_rows, configured_project):
    task_name = "test_task"
    media_attributes = True
    params = {"media_attributes": media_attributes, "predictions": True}
    task_results = _model_run_export_v2_results(model_run_with_data_rows,
                                                task_name, params)
    label_ids = [label.uid for label in configured_project.labels()]
    label_ids_set = set(label_ids)

    assert len(task_results) == len(label_ids)

    for task_result in task_results:
        # Check export param handling
        if media_attributes:
            assert 'media_attributes' in task_result and task_result[
                'media_attributes'] is not None
        else:
            assert 'media_attributes' not in task_result or task_result[
                'media_attributes'] is None
        model_run = task_result['experiments'][
            model_run_with_data_rows.model_id]['runs'][
                model_run_with_data_rows.uid]
        task_label_ids_set = set(
            map(lambda label: label['id'], model_run['labels']))
        task_prediction_ids_set = set(
            map(lambda prediction: prediction['id'], model_run['predictions']))
        for label_id in task_label_ids_set:
            assert label_id in label_ids_set
        for prediction_id in task_prediction_ids_set:
            assert prediction_id in label_ids_set
