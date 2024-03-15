from labelbox import UniqueIds, OntologyBuilder, LabelingFrontend
from labelbox.schema.conflict_resolution_strategy import ConflictResolutionStrategy


def test_send_to_annotate_include_annotations(
        client, configured_batch_project_with_label, project_pack, ontology):
    [source_project, _, data_row, _] = configured_batch_project_with_label
    destination_project = project_pack[0]

    src_ontology = source_project.ontology()
    destination_project.setup_editor(ontology)

    # build an ontology mapping using the top level tools
    src_feature_schema_ids = list(
        tool.feature_schema_id for tool in src_ontology.tools())
    dest_ontology = destination_project.ontology()
    dest_feature_schema_ids = list(
        tool.feature_schema_id for tool in dest_ontology.tools())
    # create a dictionary of feature schema id to itself
    ontology_mapping = dict(zip(src_feature_schema_ids,
                                dest_feature_schema_ids))

    try:
        queues = destination_project.task_queues()
        initial_review_task = next(
            q for q in queues if q.name == "Initial review task")

        # Send the data row to the new project
        task = client.send_to_annotate_from_catalog(
            destination_project_id=destination_project.uid,
            task_queue_id=initial_review_task.uid,
            batch_name="test-batch",
            data_rows=UniqueIds([data_row.uid]),
            params={
                "source_project_id":
                    source_project.uid,
                "annotations_ontology_mapping":
                    ontology_mapping,
                "override_existing_annotations_rule":
                    ConflictResolutionStrategy.OverrideWithAnnotations
            })

        task.wait_till_done()

        # Check that the data row was sent to the new project
        destination_batches = list(destination_project.batches())
        assert len(destination_batches) == 1

        destination_data_rows = list(destination_batches[0].export_data_rows())
        assert len(destination_data_rows) == 1
        assert destination_data_rows[0].uid == data_row.uid

        # Verify annotations were copied into the destination project
        destination_project_labels = (list(destination_project.labels()))
        assert len(destination_project_labels) == 1
    finally:
        destination_project.delete()
