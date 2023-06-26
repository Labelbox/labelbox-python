import datetime
import itertools
import time
import pytest
import uuid

import labelbox as lb
from labelbox.data.annotation_types.data.video import VideoData
from labelbox.schema.data_row import DataRow
from labelbox.schema.media_type import MediaType
import labelbox.types as lb_types
from labelbox.data.annotation_types.data import AudioData, ConversationData, DicomData, DocumentData, HTMLData, ImageData, TextData
from labelbox.data.serialization import NDJsonConverter
from labelbox.schema.annotation_import import AnnotationImportState
from utils import remove_keys_recursive, rename_cuid_key_recursive

radio_annotation = lb_types.ClassificationAnnotation(
    name="radio",
    value=lb_types.Radio(answer=lb_types.ClassificationAnswer(
        name="second_radio_answer")))
checklist_annotation = lb_types.ClassificationAnnotation(
    name="checklist",
    value=lb_types.Checklist(answer=[
        lb_types.ClassificationAnswer(name="option1"),
        lb_types.ClassificationAnswer(name="option2")
    ]))
text_annotation = lb_types.ClassificationAnnotation(
    name="text", value=lb_types.Text(answer="sample text"))

video_mask_annotation = lb_types.VideoMaskAnnotation(frames=[
    lb_types.MaskFrame(
        index=10,
        instance_uri=
        "https://storage.googleapis.com/labelbox-datasets/video-sample-data/mask_example.png"
    )
],
                                                     instances=[
                                                         lb_types.MaskInstance(
                                                             color_rgb=(255,
                                                                        255,
                                                                        255),
                                                             name=
                                                             "segmentation_mask"
                                                         )
                                                     ])

test_params = [[
    'html', lb_types.HTMLData,
    [radio_annotation, checklist_annotation, text_annotation]
],
               [
                   'audio', lb_types.AudioData,
                   [radio_annotation, checklist_annotation, text_annotation]
               ], ['video', lb_types.VideoData, [video_mask_annotation]]]


def get_annotation_comparison_dicts_from_labels(labels):
    labels_ndjson = list(NDJsonConverter.serialize(labels))
    for annotation in labels_ndjson:
        annotation.pop('uuid')
        annotation.pop('dataRow')

        if 'masks' in annotation:
            for frame in annotation['masks']['frames']:
                frame.pop('instanceURI')
            for instance in annotation['masks']['instances']:
                instance.pop('colorRGB')
    return labels_ndjson


def get_annotation_comparison_dicts_from_export(export_result, data_row_id,
                                                project_id):
    exported_data_row = [
        dr for dr in export_result if dr['data_row']['id'] == data_row_id
    ][0]
    exported_label = exported_data_row['projects'][project_id]['labels'][0]
    exported_annotations = exported_label['annotations']
    converted_annotations = []
    if exported_label['label_kind'] == 'Video':
        frames = []
        instances = []
        for frame_id, frame in exported_annotations['frames'].items():
            frames.append({'index': int(frame_id)})
            for object in frame['objects'].values():
                instances.append({'name': object['name']})
        converted_annotations.append(
            {'masks': {
                'frames': frames,
                'instances': instances,
            }})
    else:
        exported_annotations = list(
            itertools.chain(*exported_annotations.values()))
        for annotation in exported_annotations:
            if annotation['name'] == 'radio':
                converted_annotations.append({
                    'name': annotation['name'],
                    'answer': {
                        'name': annotation['radio_answer']['name']
                    }
                })
            elif annotation['name'] == 'checklist':
                converted_annotations.append({
                    'name':
                        annotation['name'],
                    'answer': [{
                        'name': answer['name']
                    } for answer in annotation['checklist_answers']]
                })
            elif annotation['name'] == 'text':
                converted_annotations.append({
                    'name': annotation['name'],
                    'answer': annotation['text_answer']['content']
                })
    return converted_annotations


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


def validate_iso_format(date_string: str):
    parsed_t = datetime.datetime.fromisoformat(
        date_string)  #this will blow up if the string is not in iso format
    assert parsed_t.hour is not None
    assert parsed_t.minute is not None
    assert parsed_t.second is not None


def to_pascal_case(name: str) -> str:
    return "".join([word.capitalize() for word in name.split("_")])


@pytest.mark.parametrize('data_type_class', [
    AudioData, HTMLData, ImageData, TextData, VideoData, ConversationData,
    DocumentData, DicomData
])
def test_import_data_types_v2(client, configured_project,
                              data_row_json_by_data_type,
                              annotations_by_data_type_v2, data_type_class,
                              exports_v2_by_data_type, export_v2_test_helpers,
                              wait_for_data_row_processing):

    project_id = configured_project.uid

    data_type_string = data_type_class.__name__[:-4].lower()

    media_type = to_pascal_case(data_type_string)
    if media_type == 'Conversation':
        media_type = 'Conversational'
    configured_project.update(media_type=MediaType[media_type])

    data_row_ndjson = data_row_json_by_data_type[data_type_string]
    dataset = next(configured_project.datasets())
    data_row = dataset.create_data_row(data_row_ndjson)
    data_row = wait_for_data_row_processing(client, data_row)

    annotations_ndjson = annotations_by_data_type_v2[data_type_string]
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

    for label in configured_project.labels():  #trigger review creation
        label.create_review(score=1.0)

    #TODO need to migrate project to the new BATCH mode and change this code
    # to be similar to tests/integration/test_task_queue.py

    result = export_v2_test_helpers.run_project_export_v2_task(
        configured_project)
    exported_data = result[0]

    # timestamp fields are in iso format
    validate_iso_format(exported_data['data_row']['details']['created_at'])
    validate_iso_format(exported_data['data_row']['details']['updated_at'])
    validate_iso_format(exported_data['projects'][project_id]['labels'][0]
                        ['label_details']['created_at'])
    validate_iso_format(exported_data['projects'][project_id]['labels'][0]
                        ['label_details']['updated_at'])
    validate_iso_format(exported_data['projects'][project_id]['labels'][0]
                        ['label_details']['reviews'][0]['reviewed_at'])
    # to be added once we have switched to the new BATCH mode
    # validate_iso_format(exported_data['projects'][project_id]['project_details']['workflow_history'][0]['created_at'])

    assert (exported_data['data_row']['id'] == data_row.uid)
    exported_project = exported_data['projects'][project_id]
    exported_project_labels = exported_project['labels'][0]
    exported_annotations = exported_project_labels['annotations']

    remove_keys_recursive(exported_annotations,
                          ['feature_id', 'feature_schema_id'])
    rename_cuid_key_recursive(exported_annotations)
    assert exported_annotations == exports_v2_by_data_type[data_type_string]

    data_row = client.get_data_row(data_row.uid)
    data_row.delete()


@pytest.mark.parametrize('data_type, data_class, annotations', test_params)
def test_import_label_annotations(client, configured_project,
                                  data_row_json_by_data_type, data_type,
                                  data_class, annotations):

    dataset = next(configured_project.datasets())
    data_row_json = data_row_json_by_data_type[data_type]
    data_row = dataset.create_data_row(data_row_json)

    labels = [
        lb_types.Label(data=data_class(uid=data_row.uid),
                       annotations=annotations)
    ]

    label_import = lb.LabelImport.create_from_objects(client,
                                                      configured_project.uid,
                                                      f'test-import-html',
                                                      labels)
    label_import.wait_until_done()

    assert label_import.state == lb.AnnotationImportState.FINISHED
    assert len(label_import.errors) == 0
    export_params = {
        "attachments": False,
        "metadata_fields": False,
        "data_row_details": False,
        "project_details": False,
        "performance_details": False
    }
    export_task = configured_project.export_v2(params=export_params)
    export_task.wait_till_done()
    assert export_task.errors is None
    expected_annotations = get_annotation_comparison_dicts_from_labels(labels)
    actual_annotations = get_annotation_comparison_dicts_from_export(
        export_task.result, data_row.uid, configured_project.uid)
    assert actual_annotations == expected_annotations
    data_row.delete()


@pytest.mark.parametrize('data_type, data_class, annotations', test_params)
def test_import_mal_annotations(client, configured_project_without_data_rows,
                                data_row_json_by_data_type, data_type,
                                data_class, annotations, rand_gen):

    dataset = client.create_dataset(name=rand_gen(str))
    data_row_json = data_row_json_by_data_type[data_type]
    data_row = dataset.create_data_row(data_row_json)

    configured_project_without_data_rows.create_batch(
        rand_gen(str),
        [data_row.uid],
    )

    labels = [
        lb_types.Label(data=data_class(uid=data_row.uid),
                       annotations=annotations)
    ]

    import_annotations = lb.MALPredictionImport.create_from_objects(
        client=client,
        project_id=configured_project_without_data_rows.uid,
        name=f"import {str(uuid.uuid4())}",
        predictions=labels)
    import_annotations.wait_until_done()

    assert import_annotations.errors == []
    # MAL Labels cannot be exported and compared to input labels
