from collections import namedtuple
from datetime import datetime
import os
from random import randint
import re
from string import ascii_letters

import pytest

from labelbox import Client


IMG_URL = "https://picsum.photos/200/300"


class IntegrationClient(Client):

    def __init__(self):
        api_url = os.environ.get("LABELBOX_TEST_ENDPOINT",
                                 "https://staging-api.labelbox.com/graphql")
        super().__init__(os.environ["LABELBOX_TEST_API_KEY"], api_url)

        self.queries = []

    def execute(self, query, params=None, check_naming=True, **kwargs):
        if check_naming:
            assert re.match(r"(?:query|mutation) \w+PyApi", query) is not None
        self.queries.append((query, params))
        return super().execute(query, params, **kwargs)


@pytest.fixture
def client():
    return IntegrationClient()


@pytest.fixture
def rand_gen():
    def gen(field_type):
        if field_type is str:
            return "".join(ascii_letters[randint(0, len(ascii_letters) - 1)]
                            for _ in range(16))

        if field_type is datetime:
            return datetime.now()

        raise Exception("Can't random generate for field type '%r'" %
                        field_type)

    return gen


@pytest.fixture
def project(client, rand_gen):
    project = client.create_project(name=rand_gen(str))
    yield project
    project.delete()


@pytest.fixture
def dataset(client, rand_gen):
    dataset = client.create_dataset(name=rand_gen(str))
    yield dataset
    dataset.delete()


LabelPack = namedtuple("LabelPack", "project dataset data_row label")


@pytest.fixture
def label_pack(project, rand_gen):
    client = project.client
    dataset = client.create_dataset(name=rand_gen(str), projects=project)
    data_row = dataset.create_data_row(row_data=IMG_URL)
    label = project.create_label(data_row=data_row, label=rand_gen(str))
    yield LabelPack(project, dataset, data_row, label)
    dataset.delete()
