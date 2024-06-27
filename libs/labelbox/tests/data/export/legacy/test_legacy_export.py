import uuid
import datetime
import time
import requests
import pytest

from labelbox.data.annotation_types.annotation import ObjectAnnotation
from labelbox.schema.annotation_import import LabelImport
from labelbox import Dataset, Project

IMAGE_URL = "https://storage.googleapis.com/lb-artifacts-testing-public/sdk_integration_test/potato.jpeg"


@pytest.mark.skip(reason="broken export v1 api, to be retired soon")
def test_export_annotations_nested_checklist(
        client, configured_project_with_complex_ontology,
        wait_for_data_row_processing):
    project, data_row = configured_project_with_complex_ontology
    data_row = wait_for_data_row_processing(client, data_row)
    ontology = project.ontology().normalized

    tool = ontology["tools"][0]

    nested_check = [
        subc for subc in tool["classifications"]
        if subc["name"] == "test-checklist-class"
    ][0]

    data = [{
        "uuid":
            str(uuid.uuid4()),
        "schemaId":
            tool['featureSchemaId'],
        "dataRow": {
            "id": data_row.uid
        },
        "bbox": {
            "top": 20,
            "left": 20,
            "height": 50,
            "width": 50
        },
        "classifications": [{
            "schemaId":
                nested_check["featureSchemaId"],
            "answers": [
                {
                    "schemaId": nested_check["options"][0]["featureSchemaId"]
                },
                {
                    "schemaId": nested_check["options"][1]["featureSchemaId"]
                },
            ]
        }]
    }]
    task = LabelImport.create_from_objects(client, project.uid,
                                           f'label-import-{uuid.uuid4()}', data)
    task.wait_until_done()
    labels = project.label_generator()
    object_annotation = [
        annot for annot in next(labels).annotations
        if isinstance(annot, ObjectAnnotation)
    ][0]

    nested_class_answers = object_annotation.classifications[0].value.answer
    assert len(nested_class_answers) == 2


@pytest.mark.skip(reason="broken export v1 api, to be retired soon")
def test_export_filtered_dates(client,
                               configured_project_with_complex_ontology):
    project, data_row = configured_project_with_complex_ontology
    ontology = project.ontology().normalized

    tool = ontology["tools"][0]

    data = [{
        "uuid": str(uuid.uuid4()),
        "schemaId": tool['featureSchemaId'],
        "dataRow": {
            "id": data_row.uid
        },
        "bbox": {
            "top": 20,
            "left": 20,
            "height": 50,
            "width": 50
        }
    }]

    task = LabelImport.create_from_objects(client, project.uid,
                                           f'label-import-{uuid.uuid4()}', data)
    task.wait_until_done()

    regular_export = project.export_labels(download=True)
    assert len(regular_export) == 1

    filtered_export = project.export_labels(download=True, start="2020-01-01")
    assert len(filtered_export) == 1

    filtered_export_with_time = project.export_labels(
        download=True, start="2020-01-01 00:00:01")
    assert len(filtered_export_with_time) == 1

    empty_export = project.export_labels(download=True,
                                         start="2020-01-01",
                                         end="2020-01-02")
    assert len(empty_export) == 0


@pytest.mark.skip(reason="broken export v1 api, to be retired soon")
def test_export_filtered_activity(client,
                                  configured_project_with_complex_ontology):
    project, data_row = configured_project_with_complex_ontology
    ontology = project.ontology().normalized

    tool = ontology["tools"][0]

    data = [{
        "uuid": str(uuid.uuid4()),
        "schemaId": tool['featureSchemaId'],
        "dataRow": {
            "id": data_row.uid
        },
        "bbox": {
            "top": 20,
            "left": 20,
            "height": 50,
            "width": 50
        }
    }]

    task = LabelImport.create_from_objects(client, project.uid,
                                           f'label-import-{uuid.uuid4()}', data)
    task.wait_until_done()

    regular_export = project.export_labels(download=True)
    assert len(regular_export) == 1

    filtered_export = project.export_labels(
        download=True,
        last_activity_start="2020-01-01",
        last_activity_end=(datetime.datetime.now() +
                           datetime.timedelta(days=2)).strftime("%Y-%m-%d"))
    assert len(filtered_export) == 1

    filtered_export_with_time = project.export_labels(
        download=True, last_activity_start="2020-01-01 00:00:01")
    assert len(filtered_export_with_time) == 1

    empty_export = project.export_labels(
        download=True,
        last_activity_start=(datetime.datetime.now() +
                             datetime.timedelta(days=2)).strftime("%Y-%m-%d"),
    )

    empty_export = project.export_labels(
        download=True,
        last_activity_end=(datetime.datetime.now() -
                           datetime.timedelta(days=1)).strftime("%Y-%m-%d"))
    assert len(empty_export) == 0


def test_export_data_rows(project: Project, dataset: Dataset):
    n_data_rows = 2
    task = dataset.create_data_rows([
        {
            "row_data": IMAGE_URL,
            "external_id": "my-image"
        },
    ] * n_data_rows)
    task.wait_till_done()

    data_rows = [dr.uid for dr in list(dataset.export_data_rows())]
    batch = project.create_batch("batch test", data_rows)
    result = list(batch.export_data_rows())
    exported_data_rows = [dr.uid for dr in result]

    assert len(result) == n_data_rows
    assert set(data_rows) == set(exported_data_rows)


def test_queued_data_row_export(configured_project):
    result = configured_project.export_queued_data_rows()
    assert len(result) == 1


@pytest.mark.skip(reason="broken export v1 api, to be retired soon")
def test_label_export(configured_project_with_label):
    project, _, _, label = configured_project_with_label
    label_id = label.uid
    # Wait for exporter to retrieve latest labels
    time.sleep(10)

    # TODO: Move to export_v2
    exported_labels_url = project.export_labels()
    assert exported_labels_url is not None
    exported_labels = requests.get(exported_labels_url)
    labels = [example['ID'] for example in exported_labels.json()]
    assert labels[0] == label_id
    #TODO: Add test for bulk export back.
    # The new exporter doesn't work with the create_label mutation


def test_issues_export(project):
    exported_issues_url = project.export_issues()
    assert exported_issues_url

    exported_issues_url = project.export_issues("Open")
    assert exported_issues_url
    assert "?status=Open" in exported_issues_url

    exported_issues_url = project.export_issues("Resolved")
    assert exported_issues_url
    assert "?status=Resolved" in exported_issues_url

    invalidStatusValue = "Closed"
    with pytest.raises(ValueError) as exc_info:
        exported_issues_url = project.export_issues(invalidStatusValue)
    assert "status must be in" in str(exc_info.value)
    assert "Found %s" % (invalidStatusValue) in str(exc_info.value)


def test_dataset_export(dataset, image_url):
    n_data_rows = 2
    ids = set()
    for _ in range(n_data_rows):
        ids.add(dataset.create_data_row(row_data=image_url))
    result = list(dataset.export_data_rows())
    assert len(result) == n_data_rows
    assert set(result) == ids


@pytest.mark.skip(reason="broken export v1 api, to be retired soon")
def test_data_row_export_with_empty_media_attributes(
        client, configured_project_with_label, wait_for_data_row_processing):
    project, _, data_row, _ = configured_project_with_label
    data_row = wait_for_data_row_processing(client, data_row)
    labels = list(project.label_generator())
    assert len(
        labels
    ) == 1, "Label export job unexpectedly returned an empty result set`"
    assert labels[0].data.media_attributes == {}
