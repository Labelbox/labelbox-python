import uuid

import ndjson
import pytest
import requests

from labelbox.exceptions import UuidError
from labelbox.schema.bulk_import_request import BulkImportRequest, UuidError
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


def test_create_from_url(project):
    name = str(uuid.uuid4())
    url = "https://storage.googleapis.com/labelbox-public-bucket/predictions_test_v2.ndjson"

    bulk_import_request = project.upload_annotations(name=name, annotations=url)

    assert bulk_import_request.project() == project
    assert bulk_import_request.name == name
    assert bulk_import_request.input_file_url == url
    assert bulk_import_request.error_file_url is None
    assert bulk_import_request.status_file_url is None
    assert bulk_import_request.state == BulkImportRequestState.RUNNING


def test_create_from_objects(project):
    name = str(uuid.uuid4())

    bulk_import_request = project.upload_annotations(name=name,
                                                     annotations=PREDICTIONS)

    assert bulk_import_request.project() == project
    assert bulk_import_request.name == name
    assert bulk_import_request.error_file_url is None
    assert bulk_import_request.status_file_url is None
    assert bulk_import_request.state == BulkImportRequestState.RUNNING
    __assert_file_content(bulk_import_request.input_file_url)


def test_create_from_local_file(tmp_path, project):
    name = str(uuid.uuid4())
    file_name = f"{name}.ndjson"
    file_path = tmp_path / file_name
    with file_path.open("w") as f:
        ndjson.dump(PREDICTIONS, f)

    bulk_import_request = project.upload_annotations(name=name,
                                                     annotations=str(file_path))

    assert bulk_import_request.project() == project
    assert bulk_import_request.name == name
    assert bulk_import_request.error_file_url is None
    assert bulk_import_request.status_file_url is None
    assert bulk_import_request.state == BulkImportRequestState.RUNNING
    __assert_file_content(bulk_import_request.input_file_url)


def test_get(client, project):
    name = str(uuid.uuid4())
    url = "https://storage.googleapis.com/labelbox-public-bucket/predictions_test_v2.ndjson"
    project.upload_annotations(name=name, annotations=url)

    bulk_import_request = BulkImportRequest.from_name(client,
                                                      project_id=project.uid,
                                                      name=name)

    assert bulk_import_request.project() == project
    assert bulk_import_request.name == name
    assert bulk_import_request.input_file_url == url
    assert bulk_import_request.error_file_url is None
    assert bulk_import_request.status_file_url is None
    assert bulk_import_request.state == BulkImportRequestState.RUNNING


def test_validate_ndjson(tmp_path, project):
    file_name = f"broken.ndjson"
    file_path = tmp_path / file_name
    with file_path.open("w") as f:
        f.write("test")

    with pytest.raises(ValueError):
        project.upload_annotations(name="name", annotations=str(file_path))


def test_validate_ndjson_uuid(tmp_path, project):
    file_name = f"repeat_uuid.ndjson"
    file_path = tmp_path / file_name
    repeat_uuid = PREDICTIONS.copy()
    repeat_uuid[0]['uuid'] = 'test_uuid'
    repeat_uuid[1]['uuid'] = 'test_uuid'

    with file_path.open("w") as f:
        ndjson.dump(repeat_uuid, f)

    with pytest.raises(UuidError):
        project.upload_annotations(name="name", annotations=str(file_path))

    with pytest.raises(UuidError):
        project.upload_annotations(name="name", annotations=repeat_uuid)


@pytest.mark.slow
def test_wait_till_done(project):
    name = str(uuid.uuid4())
    url = "https://storage.googleapis.com/labelbox-public-bucket/predictions_test_v2.ndjson"
    bulk_import_request = project.upload_annotations(
        name=name,
        annotations=url,
    )

    bulk_import_request.wait_until_done()

    assert (bulk_import_request.state == BulkImportRequestState.FINISHED or
            bulk_import_request.state == BulkImportRequestState.FAILED)


def __assert_file_content(url: str):
    response = requests.get(url)
    assert response.text == ndjson.dumps(PREDICTIONS)
