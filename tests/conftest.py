import glob
from datetime import datetime
from random import randint
from string import ascii_letters

import pytest

pytest_plugins = [
    fixture_file.replace("tests/", "").replace("/", ".").replace(".py", "")
    for fixture_file in glob.glob(
        "tests/integration/annotation_import/fixtures/[!__]*.py",)
]


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
