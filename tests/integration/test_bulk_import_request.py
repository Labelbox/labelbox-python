import uuid
from attr import validate

import ndjson
import pytest
import requests

from labelbox.exceptions import UuidError
from labelbox.schema.bulk_import_request import BulkImportRequest
from labelbox.schema.enums import BulkImportRequestState

"""
- Here we only want to check that the uploads are calling the validation
- Then with unit tests we can check the types of errors raised

"""


def test_create_from_url(configured_project):
    name = str(uuid.uuid4())
    url = "https://storage.googleapis.com/labelbox-public-bucket/predictions_test_v2.ndjson"

    bulk_import_request = configured_project.upload_annotations(name=name, annotations=url, validate = False)

    assert bulk_import_request.project() == configured_project
    assert bulk_import_request.name == name
    assert bulk_import_request.input_file_url == url
    assert bulk_import_request.error_file_url is None
    assert bulk_import_request.status_file_url is None
    assert bulk_import_request.state == BulkImportRequestState.RUNNING

"""
def test_validate_file(client, configured_project):
    name = str(uuid.uuid4())
    url = "https://storage.googleapis.com/labelbox-public-bucket/predictions_test_v2.ndjson"
    configured_project.upload_annotations(name=name, annotations=url)
    with pytest.raises(ValueError):
        configured_project.upload_annotations(name=name, annotations=url, validate = True)
        #Schema ids shouldn't match
"""
    

def test_create_from_objects(configured_project, predictions):
    name = str(uuid.uuid4())
   
    bulk_import_request = configured_project.upload_annotations(name=name,
                                                     annotations=predictions)

    assert bulk_import_request.project() == configured_project
    assert bulk_import_request.name == name
    assert bulk_import_request.error_file_url is None
    assert bulk_import_request.status_file_url is None
    assert bulk_import_request.state == BulkImportRequestState.RUNNING
    __assert_file_content(bulk_import_request.input_file_url, predictions)


def test_create_from_local_file(tmp_path, predictions, configured_project):
    name = str(uuid.uuid4())
    file_name = f"{name}.ndjson"
    file_path = tmp_path / file_name
    with file_path.open("w") as f:
        ndjson.dump(predictions, f)

    bulk_import_request = configured_project.upload_annotations(name=name,
                                                     annotations=str(file_path), validate = False)

    assert bulk_import_request.project() == configured_project
    assert bulk_import_request.name == name
    assert bulk_import_request.error_file_url is None
    assert bulk_import_request.status_file_url is None
    assert bulk_import_request.state == BulkImportRequestState.RUNNING
    __assert_file_content(bulk_import_request.input_file_url, predictions)


def test_get(client, configured_project):
    name = str(uuid.uuid4())
    url = "https://storage.googleapis.com/labelbox-public-bucket/predictions_test_v2.ndjson"
    configured_project.upload_annotations(name=name, annotations=url, validate = False)

    bulk_import_request = BulkImportRequest.from_name(client,
                                                      project_id=configured_project.uid,
                                                      name=name
                                                      )

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
        configured_project.upload_annotations(name="name", annotations=str(file_path))


def test_validate_ndjson_uuid(tmp_path, configured_project, predictions):
    file_name = f"repeat_uuid.ndjson"
    file_path = tmp_path / file_name
    repeat_uuid = predictions.copy()
    repeat_uuid[0]['uuid'] = 'test_uuid'
    repeat_uuid[1]['uuid'] = 'test_uuid'

    with file_path.open("w") as f:
        ndjson.dump(repeat_uuid, f)

    with pytest.raises(UuidError):
        configured_project.upload_annotations(name="name", annotations=str(file_path))

    with pytest.raises(UuidError):
        configured_project.upload_annotations(name="name", annotations=repeat_uuid)


@pytest.mark.slow
def test_wait_till_done(configured_project):
    name = str(uuid.uuid4())
    url = "https://storage.googleapis.com/labelbox-public-bucket/predictions_test_v2.ndjson"
    bulk_import_request = configured_project.upload_annotations(
        name=name,
        annotations=url,
        validate = False
    )

    bulk_import_request.wait_until_done()

    assert (bulk_import_request.state == BulkImportRequestState.FINISHED or
            bulk_import_request.state == BulkImportRequestState.FAILED)


def __assert_file_content(url: str, predictions):
    response = requests.get(url)
    assert response.text == ndjson.dumps(predictions)
