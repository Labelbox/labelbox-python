"""For integration tests to detect the environment they are being run against.

"""
from enum import Enum
import os


class Environ(Enum):
    PROD = 'prod'
    STAGING = 'staging'


def get_environ() -> Environ:
    """
    Checks environment variables for LABELBOX_ENVIRON to be
    'prod' or 'staging'

    Make sure to set LABELBOX_TEST_ENVIRON in .github/workflows/python-package.yaml

    """
    return Environ(os.environ.get['LABELBOX_TEST_ENVIRON'])
