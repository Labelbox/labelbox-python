import os
import re
import uuid
import time
from datetime import datetime
from enum import Enum
from random import randint
from string import ascii_letters

import pytest

IMG_URL = "https://picsum.photos/200/300"


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
