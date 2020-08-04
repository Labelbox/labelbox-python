import uuid

import ndjson
import pytest
import requests

from labelbox.schema.bulk_import_request import BulkImportRequest
from labelbox.schema.enums import BulkImportRequestState

PREDICTIONS = [{
    "uuid": "9fd9a92e-2560-4e77-81d4-b2e955800092",
    "schemaId": "ckappz7d700gn0zbocmqkwd9i",
    "dataRow": {
        "id": "ck1s02fqxm8fi0757f0e6qtdc"
    },
    "bbox": {
        "top": 48,
        "left": 58,
        "height": 865,
        "width": 1512
    }
}, {
    "uuid":
        "29b878f3-c2b4-4dbf-9f22-a795f0720125",
    "schemaId":
        "ckappz7d800gp0zboqdpmfcty",
    "dataRow": {
        "id": "ck1s02fqxm8fi0757f0e6qtdc"
    },
    "polygon": [{
        "x": 147.692,
        "y": 118.154
    }, {
        "x": 142.769,
        "y": 404.923
    }, {
        "x": 57.846,
        "y": 318.769
    }, {
        "x": 28.308,
        "y": 169.846
    }]
}]


def test_create_from_url(client, project):
    name = str(uuid.uuid4())
    url = "https://storage.googleapis.com/labelbox-public-bucket/predictions_test_v2.ndjson"

    bulk_import_request = BulkImportRequest.create_from_url(
        client, project.uid, name, url)

    assert bulk_import_request.project() == project
    assert bulk_import_request.name == name
    assert bulk_import_request.input_file_url == url
    assert bulk_import_request.error_file_url is None
    assert bulk_import_request.status_file_url is None
    assert bulk_import_request.state == BulkImportRequestState.RUNNING


def test_create_from_objects(client, project):
    name = str(uuid.uuid4())

    bulk_import_request = BulkImportRequest.create_from_objects(
        client, project.uid, name, PREDICTIONS)

    assert bulk_import_request.project() == project
    assert bulk_import_request.name == name
    assert bulk_import_request.error_file_url is None
    assert bulk_import_request.status_file_url is None
    assert bulk_import_request.state == BulkImportRequestState.RUNNING
    __assert_file_content(bulk_import_request.input_file_url)


def test_create_from_local_file(tmp_path, client, project):
    name = str(uuid.uuid4())
    file_name = f"{name}.ndjson"
    file_path = tmp_path / file_name
    with file_path.open("w") as f:
        ndjson.dump(PREDICTIONS, f)

    bulk_import_request = BulkImportRequest.create_from_local_file(
        client, project.uid, name, file_path)

    assert bulk_import_request.project() == project
    assert bulk_import_request.name == name
    assert bulk_import_request.error_file_url is None
    assert bulk_import_request.status_file_url is None
    assert bulk_import_request.state == BulkImportRequestState.RUNNING
    __assert_file_content(bulk_import_request.input_file_url)


def test_get(client, project):
    name = str(uuid.uuid4())
    url = "https://storage.googleapis.com/labelbox-public-bucket/predictions_test_v2.ndjson"
    BulkImportRequest.create_from_url(client, project.uid, name, url)

    bulk_import_request = BulkImportRequest.get(client, project.uid, name)

    assert bulk_import_request.project() == project
    assert bulk_import_request.name == name
    assert bulk_import_request.input_file_url == url
    assert bulk_import_request.error_file_url is None
    assert bulk_import_request.status_file_url is None
    assert bulk_import_request.state == BulkImportRequestState.RUNNING


def test_validate_ndjson(tmp_path, client, project):
    file_name = f"broken.ndjson"
    file_path = tmp_path / file_name
    with file_path.open("w") as f:
        f.write("test")

    with pytest.raises(ValueError):
        BulkImportRequest.create_from_local_file(client, project.uid, "name",
                                                 file_path)


@pytest.mark.slow
def test_wait_till_done(client, project):
    name = str(uuid.uuid4())
    url = "https://storage.googleapis.com/labelbox-public-bucket/predictions_test_v2.ndjson"
    bulk_import_request = BulkImportRequest.create_from_url(
        client, project.uid, name, url)

    bulk_import_request.wait_until_done()

    assert (bulk_import_request.state == BulkImportRequestState.FINISHED or
            bulk_import_request.state == BulkImportRequestState.FAILED)


def __assert_file_content(url: str):
    response = requests.get(url)
    assert response.text == ndjson.dumps(PREDICTIONS)
