from tempfile import NamedTemporaryFile

import pytest
import requests

from labelbox import DataRow
from labelbox.exceptions import InvalidQueryError


def test_get_data_row(datarow, client):
    assert client.get_data_row(datarow.uid)


def test_data_row_bulk_creation(dataset, rand_gen, image_url):
    client = dataset.client
    assert len(list(dataset.data_rows())) == 0

    # Test creation using URL
    task = dataset.create_data_rows([
        {
            DataRow.row_data: image_url
        },
        {
            "row_data": image_url
        },
    ])
    assert task in client.get_user().created_tasks()
    # TODO make Tasks expandable
    with pytest.raises(InvalidQueryError):
        assert task.created_by() == client.get_user()
    task.wait_till_done()
    assert task.status == "COMPLETE"

    data_rows = list(dataset.data_rows())
    assert len(data_rows) == 2
    assert {data_row.row_data for data_row in data_rows} == {image_url}

    # Test creation using file name
    with NamedTemporaryFile() as fp:
        data = rand_gen(str).encode()
        fp.write(data)
        fp.flush()
        task = dataset.create_data_rows([fp.name])
        task.wait_till_done()
        assert task.status == "COMPLETE"

        task = dataset.create_data_rows([{
            "row_data": fp.name,
            'external_id': 'some_name'
        }])
        task.wait_till_done()
        assert task.status == "COMPLETE"

        task = dataset.create_data_rows([{"row_data": fp.name}])
        task.wait_till_done()
        assert task.status == "COMPLETE"

    data_rows = list(dataset.data_rows())
    assert len(data_rows) == 5
    url = ({data_row.row_data for data_row in data_rows} - {image_url}).pop()
    assert requests.get(url).content == data

    data_rows[0].delete()


@pytest.mark.slow
def test_data_row_large_bulk_creation(dataset, image_url):
    # Do a longer task and expect it not to be complete immediately
    with NamedTemporaryFile() as fp:
        fp.write("Test data".encode())
        fp.flush()
        task = dataset.create_data_rows([{
            DataRow.row_data: image_url
        }] * 750 + [fp.name] * 250)
    assert task.status == "IN_PROGRESS"
    task.wait_till_done(timeout_seconds=120)
    assert task.status == "COMPLETE"
    assert len(list(dataset.data_rows())) == 1000


@pytest.mark.xfail(reason="DataRow.dataset() relationship not set")
def test_data_row_single_creation(dataset, rand_gen, image_url):
    client = dataset.client
    assert len(list(dataset.data_rows())) == 0

    data_row = dataset.create_data_row(row_data=image_url)
    assert len(list(dataset.data_rows())) == 1
    assert data_row.dataset() == dataset
    assert data_row.created_by() == client.get_user()
    assert data_row.organization() == client.get_organization()
    assert requests.get(image_url).content == \
        requests.get(data_row.row_data).content
    assert data_row.media_attributes is not None

    with NamedTemporaryFile() as fp:
        data = rand_gen(str).encode()
        fp.write(data)
        fp.flush()
        data_row_2 = dataset.create_data_row(row_data=fp.name)
        assert len(list(dataset.data_rows())) == 2
        assert requests.get(data_row_2.row_data).content == data


def test_data_row_update(dataset, rand_gen, image_url):
    external_id = rand_gen(str)
    data_row = dataset.create_data_row(row_data=image_url,
                                       external_id=external_id)
    assert data_row.external_id == external_id

    external_id_2 = rand_gen(str)
    data_row.update(external_id=external_id_2)
    assert data_row.external_id == external_id_2


def test_data_row_filtering_sorting(dataset, image_url):
    task = dataset.create_data_rows([
        {
            DataRow.row_data: image_url,
            DataRow.external_id: "row1"
        },
        {
            DataRow.row_data: image_url,
            DataRow.external_id: "row2"
        },
    ])
    task.wait_till_done()

    # Test filtering
    row1 = list(dataset.data_rows(where=DataRow.external_id == "row1"))
    assert len(row1) == 1
    row1 = row1[0]
    assert row1.external_id == "row1"
    row2 = list(dataset.data_rows(where=DataRow.external_id == "row2"))
    assert len(row2) == 1
    row2 = row2[0]
    assert row2.external_id == "row2"

    # Test sorting
    assert list(
        dataset.data_rows(order_by=DataRow.external_id.asc)) == [row1, row2]
    assert list(
        dataset.data_rows(order_by=DataRow.external_id.desc)) == [row2, row1]


def test_data_row_deletion(dataset, image_url):
    task = dataset.create_data_rows([{
        DataRow.row_data: image_url,
        DataRow.external_id: str(i)
    } for i in range(10)])
    task.wait_till_done()

    data_rows = list(dataset.data_rows())
    expected = set(map(str, range(10)))
    assert {dr.external_id for dr in data_rows} == expected

    for dr in data_rows:
        if dr.external_id in "37":
            dr.delete()
    expected -= set("37")

    data_rows = list(dataset.data_rows())
    assert {dr.external_id for dr in data_rows} == expected

    DataRow.bulk_delete([dr for dr in data_rows if dr.external_id in "2458"])
    expected -= set("2458")

    data_rows = list(dataset.data_rows())
    assert {dr.external_id for dr in data_rows} == expected


def test_data_row_iteration(dataset, image_url) -> None:
    task = dataset.create_data_rows([
        {
            DataRow.row_data: image_url
        },
        {
            "row_data": image_url
        },
    ])
    task.wait_till_done()
    assert next(dataset.data_rows())


def test_data_row_attachments(dataset, image_url):
    attachments = [("IMAGE", image_url), ("TEXT", "test-text"),
                   ("IMAGE_OVERLAY", image_url), ("HTML", image_url)]
    task = dataset.create_data_rows([{
        "row_data": image_url,
        "external_id": "test-id",
        "attachments": [{
            "type": attachment_type,
            "value": attachment_value
        }]
    } for attachment_type, attachment_value in attachments])

    task.wait_till_done()
    assert task.status == "COMPLETE"
    data_rows = list(dataset.data_rows())
    assert len(data_rows) == len(attachments)
    for data_row in data_rows:
        assert len(list(data_row.attachments())) == 1
        assert data_row.external_id == "test-id"

    with pytest.raises(ValueError) as exc:
        task = dataset.create_data_rows([{
            "row_data": image_url,
            "external_id": "test-id",
            "attachments": [{
                "type": "INVALID",
                "value": "123"
            }]
        }])
