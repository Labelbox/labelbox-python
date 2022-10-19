from time import sleep


def test_export_empty_media_attributes(configured_project_with_label):
    project, _, _, _ = configured_project_with_label
    # Wait for exporter to retrieve latest labels
    sleep(10)
    labels = project.label_generator()
    label = next(labels)
    assert label.data.media_attributes == {}