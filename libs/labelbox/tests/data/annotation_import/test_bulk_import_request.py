from unittest.mock import patch
import uuid
from labelbox import parser, Project
from labelbox.data.annotation_types.data.generic_data_row_data import GenericDataRowData
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

@pytest.mark.order(1)
def test_create_from_url(module_project):
    name = str(uuid.uuid4())
    url = "https://storage.googleapis.com/labelbox-public-bucket/predictions_test_v2.ndjson"

    bulk_import_request = module_project.upload_annotations(name=name,
                                                            annotations=url,
                                                            validate=False)

    assert bulk_import_request.project() == module_project
    assert bulk_import_request.name == name
    assert bulk_import_request.input_file_url == url
    assert bulk_import_request.error_file_url is None
    assert bulk_import_request.status_file_url is None
    assert bulk_import_request.state == BulkImportRequestState.RUNNING


def test_validate_file(module_project):
    name = str(uuid.uuid4())
    url = "https://storage.googleapis.com/labelbox-public-bucket/predictions_test_v2.ndjson"
    with pytest.raises(MALValidationError):
        module_project.upload_annotations(name=name,
                                          annotations=url,
                                          validate=True)
        #Schema ids shouldn't match


def test_create_from_objects(module_project: Project, predictions,
                             annotation_import_test_helpers):
    name = str(uuid.uuid4())

    bulk_import_request = module_project.upload_annotations(
        name=name, annotations=predictions[0])

    assert bulk_import_request.project() == module_project
    assert bulk_import_request.name == name
    assert bulk_import_request.error_file_url is None
    assert bulk_import_request.status_file_url is None
    assert bulk_import_request.state == BulkImportRequestState.RUNNING
    annotation_import_test_helpers.assert_file_content(
        bulk_import_request.input_file_url, predictions[0])


def test_create_from_label_objects(module_project, predictions,
                                   annotation_import_test_helpers):
    name = str(uuid.uuid4())

    labels = list(NDJsonConverter.deserialize(predictions[0]))
    bulk_import_request = module_project.upload_annotations(
        name=name, annotations=labels)

    assert bulk_import_request.project() == module_project
    assert bulk_import_request.name == name
    assert bulk_import_request.error_file_url is None
    assert bulk_import_request.status_file_url is None
    assert bulk_import_request.state == BulkImportRequestState.RUNNING
    normalized_predictions = list(NDJsonConverter.serialize(labels))
    annotation_import_test_helpers.assert_file_content(
        bulk_import_request.input_file_url, normalized_predictions)


def test_create_from_local_file(tmp_path, predictions, module_project,
                                annotation_import_test_helpers):
    name = str(uuid.uuid4())
    file_name = f"{name}.ndjson"
    file_path = tmp_path / file_name
    with file_path.open("w") as f:
        parser.dump(predictions[0], f)

    bulk_import_request = module_project.upload_annotations(
        name=name, annotations=str(file_path), validate=False)

    assert bulk_import_request.project() == module_project
    assert bulk_import_request.name == name
    assert bulk_import_request.error_file_url is None
    assert bulk_import_request.status_file_url is None
    assert bulk_import_request.state == BulkImportRequestState.RUNNING
    annotation_import_test_helpers.assert_file_content(
        bulk_import_request.input_file_url, predictions[0])


def test_get(client, module_project):
    name = str(uuid.uuid4())
    url = "https://storage.googleapis.com/labelbox-public-bucket/predictions_test_v2.ndjson"
    module_project.upload_annotations(name=name,
                               annotations=url,
                               validate=False)

    bulk_import_request = BulkImportRequest.from_name(
        client, project_id=module_project.uid, name=name)

    assert bulk_import_request.project() == module_project
    assert bulk_import_request.name == name
    assert bulk_import_request.input_file_url == url
    assert bulk_import_request.error_file_url is None
    assert bulk_import_request.status_file_url is None
    assert bulk_import_request.state == BulkImportRequestState.RUNNING


def test_validate_ndjson(tmp_path, module_project):
    file_name = f"broken.ndjson"
    file_path = tmp_path / file_name
    with file_path.open("w") as f:
        f.write("test")

    with pytest.raises(ValueError):
        module_project.upload_annotations(
            name="name", validate=True, annotations=str(file_path))


def test_validate_ndjson_uuid(tmp_path, module_project, predictions):
    file_name = f"repeat_uuid.ndjson"
    file_path = tmp_path / file_name
    repeat_uuid = predictions[0].copy()
    uid = str(uuid.uuid4())
    repeat_uuid[0]['uuid'] = uid
    repeat_uuid[1]['uuid'] = uid

    with file_path.open("w") as f:
        parser.dump(repeat_uuid, f)

    with pytest.raises(UuidError):
        module_project.upload_annotations(name="name",
                                              validate=True,
                                              annotations=str(file_path))

    with pytest.raises(UuidError):
        module_project.upload_annotations(name="name",
                                          validate=True,
                                          annotations=repeat_uuid)


@pytest.mark.skip("Slow test and uses a deprecated api endpoint for annotation imports")
def test_wait_till_done(rectangle_inference,
                        project):
    name = str(uuid.uuid4())
    url = project.client.upload_data(
        content=parser.dumps(rectangle_inference), sign=True)
    bulk_import_request = project.upload_annotations(
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


def test_project_bulk_import_requests(module_project, predictions):
    result = module_project.bulk_import_requests()
    assert len(list(result)) == 0

    name = str(uuid.uuid4())
    bulk_import_request = module_project.upload_annotations(
        name=name, annotations=predictions[0])
    bulk_import_request.wait_until_done()

    name = str(uuid.uuid4())
    bulk_import_request = module_project.upload_annotations(
        name=name, annotations=predictions[0])
    bulk_import_request.wait_until_done()

    name = str(uuid.uuid4())
    bulk_import_request = module_project.upload_annotations(
        name=name, annotations=predictions[0])
    bulk_import_request.wait_until_done()

    result = module_project.bulk_import_requests()
    assert len(list(result)) == 3


def test_delete(module_project, predictions):
    name = str(uuid.uuid4())
    
    bulk_import_requests = module_project.bulk_import_requests()
    [bulk_import_request.delete() for bulk_import_request in bulk_import_requests]
    
    bulk_import_request = module_project.upload_annotations(
        name=name, annotations=predictions[0])
    bulk_import_request.wait_until_done()
    all_import_requests = module_project.bulk_import_requests()
    assert len(list(all_import_requests)) == 1

    bulk_import_request.delete()
    all_import_requests = module_project.bulk_import_requests()
    assert len(list(all_import_requests)) == 0


def _create_label(row_index, data_row_uids, label_name_ids=['bbox']):
    label_name = label_name_ids[row_index % len(label_name_ids)]
    data_row_uid = data_row_uids[row_index % len(data_row_uids)]
    return Label(data=GenericDataRowData(uid=data_row_uid),
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


@pytest.mark.parametrize("configured_project", [MediaType.Video], indirect = True)
@patch('labelbox.schema.annotation_import.ANNOTATION_PER_LABEL_LIMIT', 20)
def test_below_annotation_limit_on_single_data_row(
        client, configured_project, video_data, rand_gen):
    _, data_row_uids = video_data
    configured_project.create_batch(
        rand_gen(str),
        data_row_uids,  # sample of data row objects
        5  # priority between 1(Highest) - 5(lowest)
    )
    labels = [_create_label(index, data_row_uids) for index in range(19)]
    import_annotations = MALPredictionImport.create_from_objects(
        client=client,
        project_id=configured_project.uid,
        name=f"import {str(uuid.uuid4())}",
        predictions=labels)
    import_annotations.wait_until_done()

    assert import_annotations.errors == []


@pytest.mark.parametrize("configured_project", [MediaType.Video], indirect = True)
@patch('labelbox.schema.annotation_import.ANNOTATION_PER_LABEL_LIMIT', 20)
def test_above_annotation_limit_on_single_label_on_single_data_row(
        client, configured_project, video_data, rand_gen):
    _, data_row_uids = video_data

    configured_project.create_batch(
        rand_gen(str),
        data_row_uids,  # sample of data row objects
        5  # priority between 1(Highest) - 5(lowest)
    )
    labels = [_create_label(index, data_row_uids) for index in range(21)]
    with pytest.raises(ValueError):
        import_annotations = MALPredictionImport.create_from_objects(
            client=client,
            project_id=configured_project.uid,
            name=f"import {str(uuid.uuid4())}",
            predictions=labels)
        import_annotations.wait_until_done()

@pytest.mark.parametrize("configured_project", [MediaType.Video], indirect = True)
@patch('labelbox.schema.annotation_import.ANNOTATION_PER_LABEL_LIMIT', 20)
def test_above_annotation_limit_divided_among_different_rows(
        client, configured_project, video_data_100_rows,
        rand_gen):
    _, data_row_uids = video_data_100_rows

    configured_project.create_batch(
        rand_gen(str),
        data_row_uids,  # sample of data row objects
        5  # priority between 1(Highest) - 5(lowest)
    )
    labels = [_create_label(index, data_row_uids) for index in range(21)]

    import_annotations = MALPredictionImport.create_from_objects(
        client=client,
        project_id=configured_project.uid,
        name=f"import {str(uuid.uuid4())}",
        predictions=labels)

    assert import_annotations.errors == []


@pytest.mark.parametrize("configured_project", [MediaType.Video], indirect = True)
@patch('labelbox.schema.annotation_import.ANNOTATION_PER_LABEL_LIMIT', 20)
def test_above_annotation_limit_divided_among_labels_on_one_row(
        client, configured_project, video_data, rand_gen):
    _, data_row_uids = video_data

    configured_project.create_batch(
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
        project_id=configured_project.uid,
        name=f"import {str(uuid.uuid4())}",
        predictions=labels)

    assert import_annotations.errors == []
