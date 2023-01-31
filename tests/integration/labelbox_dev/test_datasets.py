from labelbox_dev.dataset import Dataset


def test_get_all_datasets(dataset):
    datasets = list(Dataset.get_all())
    assert len(datasets) > 0
    assert isinstance(datasets[0], Dataset)