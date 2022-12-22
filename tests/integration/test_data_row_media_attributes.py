from time import sleep


def test_export_empty_media_attributes(configured_project_with_label):
    project, _, _, _ = configured_project_with_label
    # Wait for exporter to retrieve latest labels
    sleep(10)
    labels = project.label_generator().as_list()
    assert len(
        labels
    ) == 1, "Labels could not be fetched via `project.label_generator()`"
    assert labels[0].data.media_attributes == {}
