from tempfile import NamedTemporaryFile

import pytest

from labelbox import Project, Dataset, DataRow
from labelbox.exceptions import NetworkError


IMG_URL = "https://picsum.photos/200/300"


def test_data_row_bulk_creation(client, rand_gen):
    dataset = client.create_dataset(name=rand_gen(str))

    assert len(list(dataset.data_rows())) == 0

    # Test creation using URL
    task = dataset.create_data_rows([
        {DataRow.row_data: IMG_URL},
        {"row_data": IMG_URL},
    ])
    task.wait_till_done()
    assert task.status == "COMPLETE"

    datarows = list(dataset.data_rows())
    assert len(datarows) == 2

    # Test creation using file name
    with NamedTemporaryFile() as fp:
        fp.write("Test data".encode())
        task = dataset.create_data_rows([fp.name])
        task.wait_till_done()
        assert task.status == "COMPLETE"

    datarows = list(dataset.data_rows())
    assert len(datarows) == 3

    # Currently can't delete DataRow by setting deleted=true
    # TODO ensure DataRow can be deleted (server-side) by setting deleted=true
    # TODO should this raise NetworkError or something else
    with pytest.raises(NetworkError):
        datarows[0].delete()

    # Do a longer task and expect it not to be complete immediately
    task = dataset.create_data_rows([{DataRow.row_data: IMG_URL}] * 5000)
    assert task.status == "IN_PROGRESS"
    task.wait_till_done()
    assert task.status == "COMPLETE"
    datarows = len(list(dataset.data_rows())) == 5003

    dataset.delete()


def test_data_row_single_creation(client, rand_gen):
    dataset = client.create_dataset(name=rand_gen(str))
    assert len(list(dataset.data_rows())) == 0

    data_row = dataset.create_data_row(row_data=IMG_URL)
    assert len(list(dataset.data_rows())) == 1
    # TODO support data-row lookup on ID
    with pytest.raises(NetworkError):
        assert data_row.dataset() == dataset

    with NamedTemporaryFile() as fp:
        fp.write("Test data".encode())
        data_row_2 = dataset.create_data_row(row_data=fp.name)
        assert len(list(dataset.data_rows())) == 2

    dataset.delete()


def test_data_row_update(client, rand_gen):
    dataset = client.create_dataset(name=rand_gen(str))
    external_id = rand_gen(str)
    data_row = dataset.create_data_row(row_data=IMG_URL, external_id=external_id)
    assert data_row.external_id == external_id

    external_id_2 = rand_gen(str)
    # TODO enable DataRow updates
    with pytest.raises(NetworkError):
        data_row = data_row.update(external_id=external_id_2)
        assert data_row.external_id == external_id_2

    dataset.delete()
