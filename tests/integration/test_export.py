import uuid
import datetime

from labelbox.data.annotation_types.annotation import ObjectAnnotation
from labelbox.schema.annotation_import import LabelImport


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
