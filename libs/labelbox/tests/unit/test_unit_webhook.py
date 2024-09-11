from unittest.mock import MagicMock
import pytest

from labelbox import Webhook


def test_webhook_create_with_no_secret(rand_gen):
    client = MagicMock()
    project = MagicMock()
    secret = ""
    url = "https:/" + rand_gen(str)
    topics = []

    with pytest.raises(ValueError) as exc_info:
        Webhook.create(client, topics, url, secret, project)
    assert str(exc_info.value) == "Secret must be a non-empty string."


def test_webhook_create_with_no_topics(rand_gen):
    client = MagicMock()
    project = MagicMock()
    secret = rand_gen(str)
    url = "https:/" + rand_gen(str)
    topics = []

    with pytest.raises(ValueError) as exc_info:
        Webhook.create(client, topics, url, secret, project)
    assert str(exc_info.value) == "Topics must be a non-empty list."


def test_webhook_create_with_no_url(rand_gen):
    client = MagicMock()
    project = MagicMock()
    secret = rand_gen(str)
    url = ""
    topics = [Webhook.Topic.LABEL_CREATED, Webhook.Topic.LABEL_DELETED]

    with pytest.raises(ValueError) as exc_info:
        Webhook.create(client, topics, url, secret, project)
    assert str(exc_info.value) == "URL must be a non-empty string."
