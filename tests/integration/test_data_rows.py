from tempfile import NamedTemporaryFile

import pytest
import requests

from labelbox import DataRow
from labelbox.exceptions import InvalidQueryError

IMG_URL = "https://picsum.photos/id/829/200/300"


def test_data_row_bulk_creation(dataset, rand_gen):
    client = dataset.client
    assert len(list(dataset.data_rows())) == 0

    # Test creation using URL
    task = dataset.create_data_rows([
        {
            DataRow.row_data: IMG_URL
        },
        {
            "row_data": IMG_URL
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
    assert {data_row.row_data for data_row in data_rows} == {IMG_URL}

    # Test creation using file name
    with NamedTemporaryFile() as fp:
        data = rand_gen(str).encode()
        fp.write(data)
        fp.flush()
        task = dataset.create_data_rows([fp.name])
        task.wait_till_done()
        assert task.status == "COMPLETE"

    data_rows = list(dataset.data_rows())
    assert len(data_rows) == 3
    url = ({data_row.row_data for data_row in data_rows} - {IMG_URL}).pop()
    assert requests.get(url).content == data

    data_rows[0].delete()

    # Do a longer task and expect it not to be complete immediately
    with NamedTemporaryFile() as fp:
        fp.write("Test data".encode())
        fp.flush()
        task = dataset.create_data_rows([{
            DataRow.row_data: IMG_URL
        }] * 4500 + [fp.name] * 500)
    assert task.status == "IN_PROGRESS"
    task.wait_till_done()
    assert task.status == "COMPLETE"
    data_rows = len(list(dataset.data_rows())) == 5003


@pytest.mark.skip
def test_data_row_single_creation(dataset, rand_gen):
    client = dataset.client
    assert len(list(dataset.data_rows())) == 0

    data_row = dataset.create_data_row(row_data=IMG_URL)
    assert len(list(dataset.data_rows())) == 1
    assert data_row.dataset() == dataset
    assert data_row.created_by() == client.get_user()
    assert data_row.organization() == client.get_organization()
    assert requests.get(IMG_URL).content == \
        requests.get(data_row.row_data).content

    with NamedTemporaryFile() as fp:
        data = rand_gen(str).encode()
        fp.write(data)
        fp.flush()
        data_row_2 = dataset.create_data_row(row_data=fp.name)
        assert len(list(dataset.data_rows())) == 2
        assert requests.get(data_row_2.row_data).content == data


def test_data_row_update(dataset, rand_gen):
    external_id = rand_gen(str)
    data_row = dataset.create_data_row(row_data=IMG_URL,
                                       external_id=external_id)
    assert data_row.external_id == external_id

    external_id_2 = rand_gen(str)
    data_row.update(external_id=external_id_2)
    assert data_row.external_id == external_id_2


def test_data_row_filtering_sorting(dataset, rand_gen):
    task = dataset.create_data_rows([
        {
            DataRow.row_data: IMG_URL,
            DataRow.external_id: "row1"
        },
        {
            DataRow.row_data: IMG_URL,
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


def test_data_row_deletion(dataset, rand_gen):
    task = dataset.create_data_rows([{
        DataRow.row_data: IMG_URL,
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
