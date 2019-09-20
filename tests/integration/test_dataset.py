import pytest

from labelbox import Dataset
from labelbox.exceptions import ResourceNotFoundError


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


def test_dataset_filtering(client):
    d1 = client.create_dataset(name="d1")
    d2 = client.create_dataset(name="d2")

    assert list(client.get_datasets(where=Dataset.name=="d1")) == [d1]
    assert list(client.get_datasets(where=Dataset.name=="d2")) == [d2]

    d1.delete()
    d2.delete()
