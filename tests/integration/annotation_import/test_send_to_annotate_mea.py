import pytest

from labelbox import UniqueIds


def test_send_to_annotate_from_model(client, configured_project,
                                     model_run_predictions,
                                     model_run_with_data_rows,
                                     project_with_ontology):
    model_run = model_run_with_data_rows
    data_row_ids = [p['dataRow']['id'] for p in model_run_predictions]

    [destination_project, _] = project_with_ontology

    queues = destination_project.task_queues()
    initial_labeling_task = next(
        q for q in queues if q.name == "Initial labeling task")

    task = model_run.send_to_annotate_from_model(
        destination_project_id=destination_project.uid,
        batch_name="batch",
        data_rows=UniqueIds(data_row_ids),
        task_queue_id=initial_labeling_task.uid,
        params={})

    task.wait_till_done()

    # Check that the data row was sent to the new project
    destination_batches = list(destination_project.batches())
    assert len(destination_batches) == 1

    destination_data_rows = list(destination_batches[0].export_data_rows())
    assert len(destination_data_rows) == len(data_row_ids)
    assert all([dr.uid in data_row_ids for dr in destination_data_rows])
