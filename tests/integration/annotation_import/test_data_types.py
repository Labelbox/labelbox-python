import pytest
import labelbox as lb
import labelbox.types as lb_types
from labelbox.data.annotation_types.data import AudioData, ConversationData, DicomData, DocumentData, HTMLData, ImageData, TextData
from labelbox.data.serialization import NDJsonConverter
from labelbox.schema.annotation_import import AnnotationImportState


# TODO: Add VideoData. Currently label import job finishes without errors but project.export_labels() returns empty list.
@pytest.mark.parametrize('data_type_class', [
    AudioData, ConversationData, DicomData, DocumentData, HTMLData, ImageData,
    TextData
])
def test_import_data_types(client, configured_project,
                           data_row_json_by_data_type, annotations_by_data_type,
                           data_type_class):

    project_id = configured_project.uid

    data_type_string = data_type_class.__name__[:-4].lower()
    data_row_ndjson = data_row_json_by_data_type[data_type_string]
    dataset = next(configured_project.datasets())
    data_row = dataset.create_data_row(data_row_ndjson)

    annotations_ndjson = annotations_by_data_type[data_type_string]
    annotations_list = [
        label.annotations
        for label in NDJsonConverter.deserialize(annotations_ndjson)
    ]
    labels = [
        lb_types.Label(data=data_type_class(uid=data_row.uid),
                       annotations=annotations)
        for annotations in annotations_list
    ]

    label_import = lb.LabelImport.create_from_objects(
        client, project_id, f'test-import-{data_type_string}', labels)
    label_import.wait_until_done()

    assert label_import.state == AnnotationImportState.FINISHED
    assert len(label_import.errors) == 0
    exported_labels = configured_project.export_labels(download=True)
    objects = exported_labels[0]['Label']['objects']
    classifications = exported_labels[0]['Label']['classifications']
    assert len(objects) + len(classifications) == len(labels)
    data_row.delete()
