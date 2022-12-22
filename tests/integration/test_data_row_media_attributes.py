from time import sleep


def test_export_empty_media_attributes(configured_project_with_label):
    project, _, _, _ = configured_project_with_label
    # Wait for exporter to retrieve latest labels
    sleep(10)
    labels = list(project.label_generator())
    assert len(
        labels
    ) == 1, "Label export job unexpectedly returned an empty result set`"
    assert labels[0].data.media_attributes == {}
