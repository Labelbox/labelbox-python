import pytest
import uuid
from labelbox_dev import Session, DataRow, Dataset


@pytest.fixture(scope="session", autouse=True)
def session(environ: str, testing_api_url, testing_api_key):
    base_api_url = testing_api_url(environ)
    api_key = testing_api_key(environ)
    Session.initialize(base_api_url=base_api_url, api_key=api_key)


@pytest.fixture(scope="session")
def dataset():
    dataset = Dataset.create({"name": "Test", "description": "Test dataset"})

    yield dataset

    dataset.delete()


@pytest.fixture(scope="session")
def data_rows(dataset):
    BASE_PATH = 'https://storage.googleapis.com/labelbox-datasets/image_sample_data/image-sample-'
    data_rows_input = [{
        "row_data": f"{BASE_PATH}{i}.jpg",
        "global_key": f"{BASE_PATH}{i}.jpg" + str(uuid.uuid4()),
    } for i in range(5)]
    data_rows = DataRow.create(dataset.id, data_rows_input)

    yield data_rows

    for dr in data_rows:
        dr.delete()
