import pytest

from labelbox import Project, Dataset, DataRow
from labelbox.exceptions import NetworkError


IMG_URL = "https://picsum.photos/200/300"


def test_data_row_bulk_creation(client, rand_gen):
    project = client.create_project(name=rand_gen(Project.name))
    dataset = client.create_dataset(name=rand_gen(Project.name))

    assert len(list(dataset.data_rows())) == 0

    # TODO update when proper file upload becomes available to also
    # use local-files
    task = dataset.create_data_rows([{DataRow.row_data: IMG_URL}])
    task.wait_till_done()
    assert task.status == "COMPLETE"

    datarows = list(dataset.data_rows())
    assert len(datarows) == 1

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
    datarows = len(list(dataset.data_rows())) == 5001

    dataset.delete()
    project.delete()
