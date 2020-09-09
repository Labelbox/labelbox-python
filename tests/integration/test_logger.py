from labelbox import Client
import pytest
import logging

def test_client_log(caplog, project):  

    project.export_labels()
    assert '' == caplog.text

    with caplog.at_level(logging.DEBUG):
        project.export_labels()
        assert "label export, waiting for server..." in caplog.text
