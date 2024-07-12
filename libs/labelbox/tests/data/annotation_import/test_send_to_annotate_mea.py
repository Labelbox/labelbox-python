import pytest

from labelbox import UniqueIds, OntologyBuilder
from labelbox.schema.conflict_resolution_strategy import ConflictResolutionStrategy


def test_send_to_annotate_from_model(client, configured_project,
                                     model_run_predictions,
                                     model_run_with_data_rows, project):
    model_run = model_run_with_data_rows
    data_row_ids = list(set([p['dataRow']['id'] for p in model_run_predictions]))
    assert len(data_row_ids) > 0

    destination_project = project
    model = client.get_model(model_run.model_id)
    ontology = client.get_ontology(model.ontology_id)
    destination_project.connect_ontology(ontology)

    queues = destination_project.task_queues()
    initial_review_task = next(
        q for q in queues if q.name == "Initial review task")

    # build an ontology mapping using the top level tools and classifications
    source_ontology_builder = OntologyBuilder.from_project(configured_project)
    feature_schema_ids = list(
        tool.feature_schema_id for tool in source_ontology_builder.tools)
    # create a dictionary of feature schema id to itself
    ontology_mapping = dict(zip(feature_schema_ids, feature_schema_ids))

    classification_feature_schema_ids = list(
        classification.feature_schema_id
        for classification in source_ontology_builder.classifications)
    # create a dictionary of feature schema id to itself
    classification_ontology_mapping = dict(
        zip(classification_feature_schema_ids,
            classification_feature_schema_ids))

    # combine the two ontology mappings
    ontology_mapping.update(classification_ontology_mapping)

    task = model_run.send_to_annotate_from_model(
        destination_project_id=destination_project.uid,
        batch_name="batch",
        data_rows=UniqueIds(data_row_ids),
        task_queue_id=initial_review_task.uid,
        params={
            "predictions_ontology_mapping":
                ontology_mapping,
            "override_existing_annotations_rule":
                ConflictResolutionStrategy.OverrideWithPredictions
        })

    task.wait_till_done()

    # Check that the data row was sent to the new project
    destination_batches = list(destination_project.batches())
    assert len(destination_batches) == 1

    export_task = destination_project.export()
    export_task.wait_till_done()
    stream = export_task.get_buffered_stream()

    destination_data_rows = [dr.json["data_row"]["id"] for dr in stream]

    assert len(destination_data_rows) == len(data_row_ids)
    assert all([dr in data_row_ids for dr in destination_data_rows])

    # Since data rows were added to a review queue, predictions should be imported into the project as labels
    destination_project_labels = (list(destination_project.labels()))
    assert len(destination_project_labels) == len(data_row_ids)
