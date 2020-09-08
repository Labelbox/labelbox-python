from labelbox import Client
import pytest
import logging

def test_logging_info(caplog):
    """
    This test does a check on what is currently logged to the console. 

    Initialization of client will not produce a log unless the logging level has been downgraded to INFO or DEBUG.
    The initial level of log is defaulted to WARNING.
    """

    client = Client()
    assert "Initializing Labelbox client at 'https://api.labelbox.com/graphql'" not in caplog.text

    caplog.set_level(logging.INFO)

    client = Client()
    assert "Initializing Labelbox client at 'https://api.labelbox.com/graphql'" in caplog.text

