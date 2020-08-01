import pytest
import requests

from labelbox import Dataset
from labelbox.exceptions import ResourceNotFoundError

IMG_URL = "https://picsum.photos/200/300"


def test_dataset(client, rand_gen):
    before = list(client.get_datasets())
    for o in before:
        assert isinstance(o, Dataset)

    name = rand_gen(str)
    dataset = client.create_dataset(name=name)
    assert dataset.name == name
    assert dataset.created_by() == client.get_user()
    assert dataset.organization() == client.get_organization()

    after = list(client.get_datasets())
    assert len(after) == len(before) + 1
    assert dataset in after

    dataset = client.get_dataset(dataset.uid)
    assert dataset.name == name

    new_name = rand_gen(str)
    dataset.update(name=new_name)
    # Test local object updates.
    assert dataset.name == new_name

    # Test remote updates.
    dataset = client.get_dataset(dataset.uid)
    assert dataset.name == new_name

    # Test description
    description = rand_gen(str)
    assert dataset.description == ""
    dataset.update(description=description)
    assert dataset.description == description

    dataset.delete()
    final = list(client.get_datasets())
    assert dataset not in final
    assert set(final) == set(before)

    with pytest.raises(ResourceNotFoundError):
        dataset = client.get_dataset(dataset.uid)


def test_dataset_filtering(client, rand_gen):
    name_1 = rand_gen(str)
    name_2 = rand_gen(str)
    d1 = client.create_dataset(name=name_1)
    d2 = client.create_dataset(name=name_2)

    assert list(client.get_datasets(where=Dataset.name == name_1)) == [d1]
    assert list(client.get_datasets(where=Dataset.name == name_2)) == [d2]

    d1.delete()
    d2.delete()


def test_get_data_row_for_external_id(dataset, rand_gen):
    external_id = rand_gen(str)

    with pytest.raises(ResourceNotFoundError):
        data_row = dataset.data_row_for_external_id(external_id)

    data_row = dataset.create_data_row(row_data=IMG_URL,
                                       external_id=external_id)

    found = dataset.data_row_for_external_id(external_id)
    assert found.uid == data_row.uid
    assert found.external_id == external_id

    second = dataset.create_data_row(row_data=IMG_URL, external_id=external_id)

    with pytest.raises(ResourceNotFoundError):
        data_row = dataset.data_row_for_external_id(external_id)


def test_upload_video_file(dataset, sample_video: str) -> None:
    """
    Tests that a mp4 video can be uploaded and preserve content length
    and content type.

    """
    dataset.create_data_row(row_data=sample_video)
    task = dataset.create_data_rows([sample_video, sample_video])
    task.wait_till_done()

    with open(sample_video, 'rb') as video_f:
        content_length = len(video_f.read())

    for data_row in dataset.data_rows():
        url = data_row.row_data
        response = requests.head(url, allow_redirects=True)
        assert int(response.headers['Content-Length']) == content_length
        assert response.headers['Content-Type'] == 'video/mp4'
