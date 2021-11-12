import uuid
from labelbox.data.annotation_types.annotation import ObjectAnnotation

from labelbox.schema.annotation_import import LabelImport


def test_export_annotations_nested_checklist(
        client, configured_project_with_complex_ontology):
    project, data_row = configured_project_with_complex_ontology
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
                                           f'label-import-{uuid.uuid4()}',
                                           data)
    task.wait_until_done()
    labels = project.label_generator().as_list()
    object_annotation = [
        annot for annot in next(labels).annotations
        if isinstance(annot, ObjectAnnotation)
    ][0]

    nested_class_answers = object_annotation.classifications[0].value.answer
    assert len(nested_class_answers) == 2
