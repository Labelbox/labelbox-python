from copy import copy


def test_get_one_and_many_dataset_order(client):
    paginator = client.get_datasets()
    # confirm get_one returns first dataset
    all_datasets = list(paginator)
    get_one_dataset = copy(paginator).get_one()
    assert get_one_dataset.uid == all_datasets[0].uid

    # confirm get_many(1) returns first dataset
    get_many_datasets = copy(paginator).get_many(1)
    assert get_many_datasets[0].uid == all_datasets[0].uid
