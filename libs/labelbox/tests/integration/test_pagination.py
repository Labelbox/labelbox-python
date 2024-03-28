from copy import copy
import time

import pytest

from labelbox.schema.dataset import Dataset


@pytest.fixture
def data_for_dataset_order_test(client, rand_gen):
    name = rand_gen(str)
    dataset1 = client.create_dataset(name=name)
    dataset2 = client.create_dataset(name=name)

    yield name

    dataset1.delete()
    dataset2.delete()


def test_get_one_and_many_dataset_order(client, data_for_dataset_order_test):
    name = data_for_dataset_order_test

    paginator = client.get_datasets(where=Dataset.name == name)
    # confirm get_one returns first dataset
    all_datasets = list(paginator)
    assert len(all_datasets) == 2
    get_one_dataset = copy(paginator).get_one()
    assert get_one_dataset.uid == all_datasets[0].uid

    # confirm get_many(1) returns first dataset
    get_many_datasets = copy(paginator).get_many(1)
    assert get_many_datasets[0].uid == all_datasets[0].uid
