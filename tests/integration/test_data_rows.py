from tempfile import NamedTemporaryFile

import pytest
import requests

from labelbox import Project, Dataset, DataRow
from labelbox.exceptions import InvalidQueryError


IMG_URL = "https://picsum.photos/200/300"


def test_data_row_bulk_creation(client, rand_gen):
    dataset = client.create_dataset(name=rand_gen(str))

    assert len(list(dataset.data_rows())) == 0

    # Test creation using URL
    task = dataset.create_data_rows([
        {DataRow.row_data: IMG_URL},
        {"row_data": IMG_URL},
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
        fp.write("Test data".encode())
        fp.flush()
        task = dataset.create_data_rows([fp.name])
        task.wait_till_done()
        assert task.status == "COMPLETE"

    data_rows = list(dataset.data_rows())
    assert len(data_rows) == 3
    url = ({data_row.row_data for data_row in data_rows} - {IMG_URL}).pop()
    res = requests.get(url)
    assert res.status_code == 200
    assert res.text == "Test data"

    # Currently can't delete DataRow by setting deleted=true
    # TODO ensure DataRow can be deleted (server-side) by setting deleted=true
    with pytest.raises(InvalidQueryError):
        data_rows[0].delete()

    # Do a longer task and expect it not to be complete immediately
    with NamedTemporaryFile() as fp:
        fp.write("Test data".encode())
        fp.flush()
        task = dataset.create_data_rows(
            [{DataRow.row_data: IMG_URL}] * 4500 + [fp.name] * 500)
    assert task.status == "IN_PROGRESS"
    task.wait_till_done()
    assert task.status == "COMPLETE"
    data_rows = len(list(dataset.data_rows())) == 5003

    dataset.delete()


def test_data_row_single_creation(client, rand_gen):
    dataset = client.create_dataset(name=rand_gen(str))
    assert len(list(dataset.data_rows())) == 0

    data_row = dataset.create_data_row(row_data=IMG_URL)
    assert len(list(dataset.data_rows())) == 1
    assert data_row.dataset() == dataset
    assert data_row.created_by() == client.get_user()
    assert data_row.organization() == client.get_organization()

    with NamedTemporaryFile() as fp:
        fp.write("Test data".encode())
        data_row_2 = dataset.create_data_row(row_data=fp.name)
        assert len(list(dataset.data_rows())) == 2

    dataset.delete()


def test_data_row_delete(client, rand_gen):
    dataset = client.create_dataset(name=rand_gen(str))
    data_row = dataset.create_data_row(row_data=IMG_URL)
    assert len(list(dataset.data_rows())) == 1
    # TODO enable datarow deletions
    with pytest.raises(InvalidQueryError):
        data_row.delete()
        assert len(list(dataset.data_rows())) == 0


def test_data_row_update(client, rand_gen):
    dataset = client.create_dataset(name=rand_gen(str))
    external_id = rand_gen(str)
    data_row = dataset.create_data_row(row_data=IMG_URL, external_id=external_id)
    assert data_row.external_id == external_id

    external_id_2 = rand_gen(str)
    # TODO enable DataRow updates
    with pytest.raises(InvalidQueryError):
        data_row = data_row.update(external_id=external_id_2)
        assert data_row.external_id == external_id_2

    dataset.delete()


def test_data_row_filtering_sorting(client, rand_gen):
    dataset = client.create_dataset(name=rand_gen(str))
    task = dataset.create_data_rows([
        {DataRow.row_data: IMG_URL, DataRow.external_id: "row1"},
        {DataRow.row_data: IMG_URL, DataRow.external_id: "row2"},
    ])
    task.wait_till_done()

    # Test filtering
    row1 = list(dataset.data_rows(where=DataRow.external_id=="row1"))
    assert len(row1) == 1
    row1 = row1[0]
    assert row1.external_id == "row1"
    row2 = list(dataset.data_rows(where=DataRow.external_id=="row2"))
    assert len(row2) == 1
    row2 = row2[0]
    assert row2.external_id == "row2"

    # Test sorting
    assert list(dataset.data_rows(order_by=DataRow.external_id.asc)) == [row1, row2]
    assert list(dataset.data_rows(order_by=DataRow.external_id.desc)) == [row2, row1]

    dataset.delete()
