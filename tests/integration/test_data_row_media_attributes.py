def test_export_empty_media_attributes(client, configured_project_with_label,
                                       wait_for_data_row_processing):
    project, _, data_row, _ = configured_project_with_label
    data_row = wait_for_data_row_processing(client, data_row)
    labels = list(project.label_generator())
    assert len(
        labels
    ) == 1, "Label export job unexpectedly returned an empty result set`"
    assert labels[0].data.media_attributes == {}
