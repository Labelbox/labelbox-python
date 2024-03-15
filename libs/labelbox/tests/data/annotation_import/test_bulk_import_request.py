from unittest.mock import patch
import uuid
from labelbox import parser
import pytest
import random
from labelbox.data.annotation_types.annotation import ObjectAnnotation
from labelbox.data.annotation_types.classification.classification import Checklist, ClassificationAnnotation, ClassificationAnswer, Radio
from labelbox.data.annotation_types.data.video import VideoData
from labelbox.data.annotation_types.geometry.point import Point
from labelbox.data.annotation_types.geometry.rectangle import Rectangle, RectangleUnit
from labelbox.data.annotation_types.label import Label
from labelbox.data.annotation_types.data.text import TextData
from labelbox.data.annotation_types.ner import DocumentEntity, DocumentTextSelection
from labelbox.data.annotation_types.video import VideoObjectAnnotation

from labelbox.data.serialization import NDJsonConverter
from labelbox.exceptions import MALValidationError, UuidError
from labelbox.schema.bulk_import_request import BulkImportRequest
from labelbox.schema.enums import BulkImportRequestState
from labelbox.schema.annotation_import import LabelImport, MALPredictionImport
from labelbox.schema.media_type import MediaType
"""
- Here we only want to check that the uploads are calling the validation
- Then with unit tests we can check the types of errors raised

"""


def test_create_from_url(project):
    name = str(uuid.uuid4())
    url = "https://storage.googleapis.com/labelbox-public-bucket/predictions_test_v2.ndjson"

    bulk_import_request = project.upload_annotations(name=name,
                                                     annotations=url,
                                                     validate=False)

    assert bulk_import_request.project() == project
    assert bulk_import_request.name == name
    assert bulk_import_request.input_file_url == url
    assert bulk_import_request.error_file_url is None
    assert bulk_import_request.status_file_url is None
    assert bulk_import_request.state == BulkImportRequestState.RUNNING


def test_validate_file(project_with_empty_ontology):
    name = str(uuid.uuid4())
    url = "https://storage.googleapis.com/labelbox-public-bucket/predictions_test_v2.ndjson"
    with pytest.raises(MALValidationError):
        project_with_empty_ontology.upload_annotations(name=name,
                                                       annotations=url,
                                                       validate=True)
        #Schema ids shouldn't match


def test_create_from_objects(configured_project_with_one_data_row, predictions,
                             annotation_import_test_helpers):
    name = str(uuid.uuid4())

    bulk_import_request = configured_project_with_one_data_row.upload_annotations(
        name=name, annotations=predictions)

    assert bulk_import_request.project() == configured_project_with_one_data_row
    assert bulk_import_request.name == name
    assert bulk_import_request.error_file_url is None
    assert bulk_import_request.status_file_url is None
    assert bulk_import_request.state == BulkImportRequestState.RUNNING
    annotation_import_test_helpers.assert_file_content(
        bulk_import_request.input_file_url, predictions)


def test_create_from_label_objects(configured_project, predictions,
                                   annotation_import_test_helpers):
    name = str(uuid.uuid4())

    labels = list(NDJsonConverter.deserialize(predictions))
    bulk_import_request = configured_project.upload_annotations(
        name=name, annotations=labels)

    assert bulk_import_request.project() == configured_project
    assert bulk_import_request.name == name
    assert bulk_import_request.error_file_url is None
    assert bulk_import_request.status_file_url is None
    assert bulk_import_request.state == BulkImportRequestState.RUNNING
    normalized_predictions = list(NDJsonConverter.serialize(labels))
    annotation_import_test_helpers.assert_file_content(
        bulk_import_request.input_file_url, normalized_predictions)


def test_create_from_local_file(tmp_path, predictions, configured_project,
                                annotation_import_test_helpers):
    name = str(uuid.uuid4())
    file_name = f"{name}.ndjson"
    file_path = tmp_path / file_name
    with file_path.open("w") as f:
        parser.dump(predictions, f)

    bulk_import_request = configured_project.upload_annotations(
        name=name, annotations=str(file_path), validate=False)

    assert bulk_import_request.project() == configured_project
    assert bulk_import_request.name == name
    assert bulk_import_request.error_file_url is None
    assert bulk_import_request.status_file_url is None
    assert bulk_import_request.state == BulkImportRequestState.RUNNING
    annotation_import_test_helpers.assert_file_content(
        bulk_import_request.input_file_url, predictions)


def test_get(client, configured_project_with_one_data_row):
    name = str(uuid.uuid4())
    url = "https://storage.googleapis.com/labelbox-public-bucket/predictions_test_v2.ndjson"
    configured_project_with_one_data_row.upload_annotations(name=name,
                                                            annotations=url,
                                                            validate=False)

    bulk_import_request = BulkImportRequest.from_name(
        client, project_id=configured_project_with_one_data_row.uid, name=name)

    assert bulk_import_request.project() == configured_project_with_one_data_row
    assert bulk_import_request.name == name
    assert bulk_import_request.input_file_url == url
    assert bulk_import_request.error_file_url is None
    assert bulk_import_request.status_file_url is None
    assert bulk_import_request.state == BulkImportRequestState.RUNNING


def test_validate_ndjson(tmp_path, configured_project_with_one_data_row):
    file_name = f"broken.ndjson"
    file_path = tmp_path / file_name
    with file_path.open("w") as f:
        f.write("test")

    with pytest.raises(ValueError):
        configured_project_with_one_data_row.upload_annotations(
            name="name", validate=True, annotations=str(file_path))


def test_validate_ndjson_uuid(tmp_path, configured_project, predictions):
    file_name = f"repeat_uuid.ndjson"
    file_path = tmp_path / file_name
    repeat_uuid = predictions.copy()
    uid = str(uuid.uuid4())
    repeat_uuid[0]['uuid'] = uid
    repeat_uuid[1]['uuid'] = uid

    with file_path.open("w") as f:
        parser.dump(repeat_uuid, f)

    with pytest.raises(UuidError):
        configured_project.upload_annotations(name="name",
                                              validate=True,
                                              annotations=str(file_path))

    with pytest.raises(UuidError):
        configured_project.upload_annotations(name="name",
                                              validate=True,
                                              annotations=repeat_uuid)


@pytest.mark.slow
def test_wait_till_done(rectangle_inference,
                        configured_project_with_one_data_row):
    name = str(uuid.uuid4())
    url = configured_project_with_one_data_row.client.upload_data(
        content=parser.dumps([rectangle_inference]), sign=True)
    bulk_import_request = configured_project_with_one_data_row.upload_annotations(
        name=name, annotations=url, validate=False)

    assert len(bulk_import_request.inputs) == 1
    bulk_import_request.wait_until_done()
    assert bulk_import_request.state == BulkImportRequestState.FINISHED

    # Check that the status files are being returned as expected
    assert len(bulk_import_request.errors) == 0
    assert len(bulk_import_request.inputs) == 1
    assert bulk_import_request.inputs[0]['uuid'] == rectangle_inference['uuid']
    assert len(bulk_import_request.statuses) == 1
    assert bulk_import_request.statuses[0]['status'] == 'SUCCESS'
    assert bulk_import_request.statuses[0]['uuid'] == rectangle_inference[
        'uuid']


def test_project_bulk_import_requests(configured_project, predictions):
    result = configured_project.bulk_import_requests()
    assert len(list(result)) == 0

    name = str(uuid.uuid4())
    bulk_import_request = configured_project.upload_annotations(
        name=name, annotations=predictions)
    bulk_import_request.wait_until_done()

    name = str(uuid.uuid4())
    bulk_import_request = configured_project.upload_annotations(
        name=name, annotations=predictions)
    bulk_import_request.wait_until_done()

    name = str(uuid.uuid4())
    bulk_import_request = configured_project.upload_annotations(
        name=name, annotations=predictions)
    bulk_import_request.wait_until_done()

    result = configured_project.bulk_import_requests()
    assert len(list(result)) == 3


def test_delete(configured_project, predictions):
    name = str(uuid.uuid4())

    bulk_import_request = configured_project.upload_annotations(
        name=name, annotations=predictions)
    bulk_import_request.wait_until_done()
    all_import_requests = configured_project.bulk_import_requests()
    assert len(list(all_import_requests)) == 1

    bulk_import_request.delete()
    all_import_requests = configured_project.bulk_import_requests()
    assert len(list(all_import_requests)) == 0


def test_pdf_mal_bbox(client, configured_project_pdf):
    """
    tests pdf mal against only a bbox annotation
    """
    annotations = []
    num_annotations = 1

    for row in configured_project_pdf.export_queued_data_rows():
        for _ in range(num_annotations):
            annotations.append({
                "uuid": str(uuid.uuid4()),
                "name": "bbox",
                "dataRow": {
                    "id": row['id']
                },
                "bbox": {
                    "top": round(random.uniform(0, 300), 2),
                    "left": round(random.uniform(0, 300), 2),
                    "height": round(random.uniform(200, 500), 2),
                    "width": round(random.uniform(0, 200), 2)
                },
                "page": random.randint(0, 1),
                "unit": "POINTS"
            })
        annotations.extend([
            {  #annotations intended to test classifications
                'name': 'text',
                'answer': 'the answer to the text question',
                'uuid': 'fc1913c6-b735-4dea-bd25-c18152a4715f',
                "dataRow": {
                    "id": row['id']
                }
            },
            {
                'name': 'checklist',
                'uuid': '9d7b2e57-d68f-4388-867a-af2a9b233719',
                "dataRow": {
                    "id": row['id']
                },
                'answer': [{
                    'name': 'option1'
                }, {
                    'name': 'optionN'
                }]
            },
            {
                'name': 'radio',
                'answer': {
                    'name': 'second_radio_answer'
                },
                'uuid': 'ad60897f-ea1a-47de-b923-459339764921',
                "dataRow": {
                    "id": row['id']
                }
            },
            {  #adding this with the intention to ensure we allow page: 0 
                "uuid": str(uuid.uuid4()),
                "name": "bbox",
                "dataRow": {
                    "id": row['id']
                },
                "bbox": {
                    "top": round(random.uniform(0, 300), 2),
                    "left": round(random.uniform(0, 300), 2),
                    "height": round(random.uniform(200, 500), 2),
                    "width": round(random.uniform(0, 200), 2)
                },
                "page": 0,
                "unit": "POINTS"
            }
        ])
    import_annotations = MALPredictionImport.create_from_objects(
        client=client,
        project_id=configured_project_pdf.uid,
        name=f"import {str(uuid.uuid4())}",
        predictions=annotations)
    import_annotations.wait_until_done()

    assert import_annotations.errors == []


def test_pdf_document_entity(client, configured_project_with_one_data_row,
                             dataset_pdf_entity, rand_gen):
    # for content "Metal-insulator (MI) transitions have been one of the" in OCR JSON extract tests/assets/arxiv-pdf_data_99-word-token-pdfs_0801.3483-lb-textlayer.json
    document_text_selection = DocumentTextSelection(
        group_id="2f4336f4-a07e-4e0a-a9e1-5629b03b719b",
        token_ids=[
            "3f984bf3-1d61-44f5-b59a-9658a2e3440f",
            "3bf00b56-ff12-4e52-8cc1-08dbddb3c3b8",
            "6e1c3420-d4b7-4c5a-8fd6-ead43bf73d80",
            "87a43d32-af76-4a1d-b262-5c5f4d5ace3a",
            "e8606e8a-dfd9-4c49-a635-ad5c879c75d0",
            "67c7c19e-4654-425d-bf17-2adb8cf02c30",
            "149c5e80-3e07-49a7-ab2d-29ddfe6a38fa",
            "b0e94071-2187-461e-8e76-96c58738a52c"
        ],
        page=1)

    entities_annotation_document_entity = DocumentEntity(
        text_selections=[document_text_selection])
    entities_annotation = ObjectAnnotation(
        name="named-entity", value=entities_annotation_document_entity)

    labels = []
    _, data_row_uids = dataset_pdf_entity
    configured_project_with_one_data_row.create_batch(
        rand_gen(str),
        data_row_uids,  # sample of data row objects
        5  # priority between 1(Highest) - 5(lowest)
    )

    for data_row_uid in data_row_uids:
        labels.append(
            Label(data=TextData(uid=data_row_uid),
                  annotations=[
                      entities_annotation,
                  ]))

    import_annotations = MALPredictionImport.create_from_objects(
        client=client,
        project_id=configured_project_with_one_data_row.uid,
        name=f"import {str(uuid.uuid4())}",
        predictions=labels)
    import_annotations.wait_until_done()

    assert import_annotations.errors == []


def test_nested_video_object_annotations(client,
                                         configured_project_with_one_data_row,
                                         video_data,
                                         bbox_video_annotation_objects,
                                         rand_gen):
    labels = []
    _, data_row_uids = video_data
    configured_project_with_one_data_row.update(media_type=MediaType.Video)
    configured_project_with_one_data_row.create_batch(
        rand_gen(str),
        data_row_uids,  # sample of data row objects
        5  # priority between 1(Highest) - 5(lowest)
    )

    for data_row_uid in data_row_uids:
        labels.append(
            Label(data=VideoData(uid=data_row_uid),
                  annotations=bbox_video_annotation_objects))
    import_annotations = MALPredictionImport.create_from_objects(
        client=client,
        project_id=configured_project_with_one_data_row.uid,
        name=f"import {str(uuid.uuid4())}",
        predictions=labels)
    import_annotations.wait_until_done()

    assert import_annotations.errors == []


def _create_label(row_index, data_row_uids, label_name_ids=['bbox']):
    label_name = label_name_ids[row_index % len(label_name_ids)]
    data_row_uid = data_row_uids[row_index % len(data_row_uids)]
    return Label(data=VideoData(uid=data_row_uid),
                 annotations=[
                     VideoObjectAnnotation(name=label_name,
                                           keyframe=True,
                                           frame=4,
                                           segment_index=0,
                                           value=Rectangle(
                                               start=Point(x=100, y=100),
                                               end=Point(x=105, y=105),
                                           ))
                 ])


@patch('labelbox.schema.annotation_import.ANNOTATION_PER_LABEL_LIMIT', 20)
def test_below_annotation_limit_on_single_data_row(
        client, configured_project_with_one_data_row, video_data, rand_gen):
    _, data_row_uids = video_data
    configured_project_with_one_data_row.update(media_type=MediaType.Video)
    configured_project_with_one_data_row.create_batch(
        rand_gen(str),
        data_row_uids,  # sample of data row objects
        5  # priority between 1(Highest) - 5(lowest)
    )
    labels = [_create_label(index, data_row_uids) for index in range(19)]
    import_annotations = MALPredictionImport.create_from_objects(
        client=client,
        project_id=configured_project_with_one_data_row.uid,
        name=f"import {str(uuid.uuid4())}",
        predictions=labels)
    import_annotations.wait_until_done()

    assert import_annotations.errors == []


@patch('labelbox.schema.annotation_import.ANNOTATION_PER_LABEL_LIMIT', 20)
def test_above_annotation_limit_on_single_label_on_single_data_row(
        client, configured_project_with_one_data_row, video_data, rand_gen):
    _, data_row_uids = video_data

    configured_project_with_one_data_row.update(media_type=MediaType.Video)
    configured_project_with_one_data_row.create_batch(
        rand_gen(str),
        data_row_uids,  # sample of data row objects
        5  # priority between 1(Highest) - 5(lowest)
    )
    labels = [_create_label(index, data_row_uids) for index in range(21)]
    with pytest.raises(ValueError):
        import_annotations = MALPredictionImport.create_from_objects(
            client=client,
            project_id=configured_project_with_one_data_row.uid,
            name=f"import {str(uuid.uuid4())}",
            predictions=labels)
        import_annotations.wait_until_done()


@patch('labelbox.schema.annotation_import.ANNOTATION_PER_LABEL_LIMIT', 20)
def test_above_annotation_limit_divided_among_different_rows(
        client, configured_project_with_one_data_row, video_data_100_rows,
        rand_gen):
    _, data_row_uids = video_data_100_rows

    configured_project_with_one_data_row.update(media_type=MediaType.Video)
    configured_project_with_one_data_row.create_batch(
        rand_gen(str),
        data_row_uids,  # sample of data row objects
        5  # priority between 1(Highest) - 5(lowest)
    )
    labels = [_create_label(index, data_row_uids) for index in range(21)]

    import_annotations = MALPredictionImport.create_from_objects(
        client=client,
        project_id=configured_project_with_one_data_row.uid,
        name=f"import {str(uuid.uuid4())}",
        predictions=labels)

    assert import_annotations.errors == []


@patch('labelbox.schema.annotation_import.ANNOTATION_PER_LABEL_LIMIT', 20)
def test_above_annotation_limit_divided_among_labels_on_one_row(
        client, configured_project_with_one_data_row, video_data, rand_gen):
    _, data_row_uids = video_data

    configured_project_with_one_data_row.update(media_type=MediaType.Video)
    configured_project_with_one_data_row.create_batch(
        rand_gen(str),
        data_row_uids,  # sample of data row objects
        5  # priority between 1(Highest) - 5(lowest)
    )
    labels = [
        _create_label(index,
                      data_row_uids,
                      label_name_ids=['bbox', 'bbox_tool_with_nested_text'])
        for index in range(21)
    ]

    import_annotations = MALPredictionImport.create_from_objects(
        client=client,
        project_id=configured_project_with_one_data_row.uid,
        name=f"import {str(uuid.uuid4())}",
        predictions=labels)

    assert import_annotations.errors == []
