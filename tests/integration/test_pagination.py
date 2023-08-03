from copy import copy
import time

from labelbox.schema.dataset import Dataset


def test_get_one_and_many_dataset_order(client, rand_gen):
    started = time.time()
    name = rand_gen(str)
    dataset1 = client.create_dataset(name=name)
    dataset2 = client.create_dataset(name=name)

    paginator = client.get_datasets(where=Dataset.name == name)
    # confirm get_one returns first dataset
    all_datasets = list(paginator)
    assert len(all_datasets) == 2
    get_one_dataset = copy(paginator).get_one()
    assert get_one_dataset.uid == all_datasets[0].uid

    # confirm get_many(1) returns first dataset
    get_many_datasets = copy(paginator).get_many(1)
    assert get_many_datasets[0].uid == all_datasets[0].uid

    dataset1.delete()
    dataset2.delete()

    print(f"test_get_one_and_many_dataset_order took {time.time() - started}")
