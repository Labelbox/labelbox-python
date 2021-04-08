from collections import namedtuple
from enum import Enum
from datetime import datetime
import os
from random import randint
import re
from string import ascii_letters

import pytest

from labelbox import Client
from labelbox.schema.labeling_frontend import LabelingFrontend

IMG_URL = "https://picsum.photos/200/300"


class Environ(Enum):
    PROD = 'prod'
    STAGING = 'staging'


@pytest.fixture
def environ() -> Environ:
    """
    Checks environment variables for LABELBOX_ENVIRON to be
    'prod' or 'staging'

    Make sure to set LABELBOX_TEST_ENVIRON in .github/workflows/python-package.yaml

    """
    try:
        return Environ(os.environ['LABELBOX_TEST_ENVIRON'])
    except KeyError:
        raise Exception(f'Missing LABELBOX_TEST_ENVIRON in: {os.environ}')


def graphql_url(environ: str) -> str:
    if environ == Environ.PROD:
        return 'https://api.labelbox.com/graphql'
    return 'https://staging-api.labelbox.com/graphql'


def testing_api_key(environ: str) -> str:
    if environ == Environ.PROD:
        return os.environ["LABELBOX_TEST_API_KEY_PROD"]
    return os.environ["LABELBOX_TEST_API_KEY_STAGING"]


class IntegrationClient(Client):

    def __init__(self, environ: str) -> None:
        api_url = graphql_url(environ)
        api_key = testing_api_key(environ)
        super().__init__(api_key, api_url)

        self.queries = []

    def execute(self, query, params=None, check_naming=True, **kwargs):
        if check_naming:
            assert re.match(r"(?:query|mutation) \w+PyApi", query) is not None
        self.queries.append((query, params))
        return super().execute(query, params, **kwargs)


@pytest.fixture
def client(environ: str):
    return IntegrationClient(environ)


@pytest.fixture
def rand_gen():

    def gen(field_type):
        if field_type is str:
            return "".join(ascii_letters[randint(0,
                                                 len(ascii_letters) - 1)]
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


@pytest.fixture
def iframe_url(environ) -> str:
    if environ == Environ.PROD:
        return 'https://editor.labelbox.com'
    return 'https://staging.labelbox.dev/editor'


@pytest.fixture
def sample_video() -> str:
    path_to_video = 'tests/integration/media/cat.mp4'
    assert os.path.exists(path_to_video)
    return path_to_video


@pytest.fixture
def organization(client):
    return client.get_organization()
