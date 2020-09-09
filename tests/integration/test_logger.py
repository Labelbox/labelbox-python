from labelbox import Client
import pytest
import logging


def test_client_log(caplog, project):
    """
    This file tests that the logger will properly output to the console after updating logging level

    The default level is set to WARNING

    There is an expected output after setting logging level to DEBUG
    """

    project.export_labels()
    assert '' == caplog.text

    with caplog.at_level(logging.DEBUG):
        project.export_labels()
        assert "label export, waiting for server..." in caplog.text
