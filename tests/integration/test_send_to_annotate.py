import pytest

from labelbox import UniqueIds
from labelbox.schema.conflict_resolution_strategy import ConflictResolutionStrategy


def test_send_to_annotate_include_annotations(
        client, configured_batch_project_with_label, project_with_ontology):
    [source_project, _, data_row, _] = configured_batch_project_with_label
    [destination_project, _] = project_with_ontology

    try:
        queues = destination_project.task_queues()
        initial_labeling_task = next(
            q for q in queues if q.name == "Initial labeling task")
        print(initial_labeling_task)

        # Send the data row to the new project
        task = client.send_to_annotate_from_catalog(
            batch_name="test-batch",
            data_rows=UniqueIds([data_row.uid]),
            source_model_run_id=None,
            source_project_id=source_project.uid,
            destination_project=destination_project.uid,
            task_queue_id=initial_labeling_task.uid,
            override_existing_annotations_rule=ConflictResolutionStrategy.
            OverrideWithAnnotations)

        print(task)

        task.wait_till_done()

        # Check that the data row was sent to the new project
        destination_batches = list(destination_project.batches())
        assert len(destination_batches) == 1

        destination_data_rows = list(destination_batches[0].export_data_rows())
        assert len(destination_data_rows) == 1
        assert destination_data_rows[0].uid == data_row.uid

        destination_labels = list(destination_project.labels())
        print(destination_labels)
    finally:
        destination_project.delete()


def test_send_to_annotate_include_predictions():
    # TODO setup model run via model foundry, then add data rows to a new project
    pass
