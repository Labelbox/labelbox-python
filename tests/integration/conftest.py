from datetime import datetime
import os
from random import randint
import re
from string import ascii_letters

import pytest

from labelbox import Client
from labelbox.orm.model import Field


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
        if field_type == str:
            return "".join(ascii_letters[randint(0, len(ascii_letters) - 1)]
                            for _ in range(16))

        if field_type == datetime:
            return datetime.now()

        raise Exception("Can't random generate for field type '%r'" %
                        field.field_type)

    return gen
