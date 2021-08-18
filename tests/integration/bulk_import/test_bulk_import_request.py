import uuid
import ndjson
import pytest
import requests

from labelbox.exceptions import MALValidationError, UuidError
from labelbox.schema.bulk_import_request import BulkImportRequest
from labelbox.schema.enums import BulkImportRequestState
"""
- Here we only want to check that the uploads are calling the validation
- Then with unit tests we can check the types of errors raised

"""


def test_create_from_url(configured_project):
    name = str(uuid.uuid4())
    url = "https://storage.googleapis.com/labelbox-public-bucket/predictions_test_v2.ndjson"

    bulk_import_request = configured_project.upload_annotations(
        name=name, annotations=url, validate=False)

    assert bulk_import_request.project() == configured_project
    assert bulk_import_request.name == name
    assert bulk_import_request.input_file_url == url
    assert bulk_import_request.error_file_url is None
    assert bulk_import_request.status_file_url is None
    assert bulk_import_request.state == BulkImportRequestState.RUNNING


def test_validate_file(client, configured_project):
    name = str(uuid.uuid4())
    url = "https://storage.googleapis.com/labelbox-public-bucket/predictions_test_v2.ndjson"
    with pytest.raises(MALValidationError):
        configured_project.upload_annotations(name=name,
                                              annotations=url,
                                              validate=True)
        #Schema ids shouldn't match


def test_create_from_objects(configured_project, predictions):
    name = str(uuid.uuid4())

    bulk_import_request = configured_project.upload_annotations(
        name=name, annotations=predictions)

    assert bulk_import_request.project() == configured_project
    assert bulk_import_request.name == name
    assert bulk_import_request.error_file_url is None
    assert bulk_import_request.status_file_url is None
    assert bulk_import_request.state == BulkImportRequestState.RUNNING
    assert_file_content(bulk_import_request.input_file_url, predictions)


def test_create_from_local_file(tmp_path, predictions, configured_project):
    name = str(uuid.uuid4())
    file_name = f"{name}.ndjson"
    file_path = tmp_path / file_name
    with file_path.open("w") as f:
        ndjson.dump(predictions, f)

    bulk_import_request = configured_project.upload_annotations(
        name=name, annotations=str(file_path), validate=False)

    assert bulk_import_request.project() == configured_project
    assert bulk_import_request.name == name
    assert bulk_import_request.error_file_url is None
    assert bulk_import_request.status_file_url is None
    assert bulk_import_request.state == BulkImportRequestState.RUNNING
    assert_file_content(bulk_import_request.input_file_url, predictions)


def test_get(client, configured_project):
    name = str(uuid.uuid4())
    url = "https://storage.googleapis.com/labelbox-public-bucket/predictions_test_v2.ndjson"
    configured_project.upload_annotations(name=name,
                                          annotations=url,
                                          validate=False)

    bulk_import_request = BulkImportRequest.from_name(
        client, project_id=configured_project.uid, name=name)

    assert bulk_import_request.project() == configured_project
    assert bulk_import_request.name == name
    assert bulk_import_request.input_file_url == url
    assert bulk_import_request.error_file_url is None
    assert bulk_import_request.status_file_url is None
    assert bulk_import_request.state == BulkImportRequestState.RUNNING


def test_validate_ndjson(tmp_path, configured_project):
    file_name = f"broken.ndjson"
    file_path = tmp_path / file_name
    with file_path.open("w") as f:
        f.write("test")

    with pytest.raises(ValueError):
        configured_project.upload_annotations(name="name",
                                              annotations=str(file_path))


def test_validate_ndjson_uuid(tmp_path, configured_project, predictions):
    file_name = f"repeat_uuid.ndjson"
    file_path = tmp_path / file_name
    repeat_uuid = predictions.copy()
    uid = str(uuid.uuid4())
    repeat_uuid[0]['uuid'] = uid
    repeat_uuid[1]['uuid'] = uid

    with file_path.open("w") as f:
        ndjson.dump(repeat_uuid, f)

    with pytest.raises(UuidError):
        configured_project.upload_annotations(name="name",
                                              annotations=str(file_path))

    with pytest.raises(UuidError):
        configured_project.upload_annotations(name="name",
                                              annotations=repeat_uuid)


@pytest.mark.slow
def test_wait_till_done(rectangle_inference, configured_project):
    name = str(uuid.uuid4())
    url = configured_project.client.upload_data(content=ndjson.dumps(
        [rectangle_inference]),
                                                sign=True)
    bulk_import_request = configured_project.upload_annotations(
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


def assert_file_content(url: str, predictions):
    response = requests.get(url)
    assert response.text == ndjson.dumps(predictions)


def test_bulk_import_requests(client, configured_project, predictions):
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


def test_delete(client, configured_project, predictions):

    id_param = "project_id"
    query_str = """query bulk_import_requestsPyApi($%s: ID!) {bulkImportRequests(where: {projectId: $%s}) {id}}""" % (
        id_param, id_param)
    name = str(uuid.uuid4())

    bulk_import_request = configured_project.upload_annotations(
        name=name, annotations=predictions)
    bulk_import_request.wait_until_done()
    all_import_requests = client.execute(query_str,
                                         {id_param: configured_project.uid})
    assert len(all_import_requests['bulkImportRequests']) == 1

    bulk_import_request.delete()
    all_import_requests = client.execute(query_str,
                                         {id_param: configured_project.uid})
    assert len(all_import_requests['bulkImportRequests']) == 0
