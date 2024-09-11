import pytest

from labelbox import Webhook


def test_webhook_create_update(project, rand_gen):
    client = project.client
    url = "https:/" + rand_gen(str)
    secret = rand_gen(str)
    topics = [Webhook.LABEL_CREATED, Webhook.LABEL_DELETED]
    webhook = Webhook.create(client, topics, url, secret, project)

    assert webhook.project() == project
    assert webhook.organization() == client.get_organization()
    assert webhook.url == url
    assert webhook.topics == topics
    assert webhook.status == Webhook.ACTIVE
    assert list(project.webhooks()) == [webhook]
    assert webhook in set(client.get_organization().webhooks())

    webhook.update(status=Webhook.REVOKED, topics=[Webhook.LABEL_UPDATED])
    assert webhook.topics == [Webhook.LABEL_UPDATED]
    assert webhook.status == Webhook.REVOKED

    with pytest.raises(ValueError) as exc_info:
        webhook.update(status="invalid..")
    valid_webhook_statuses = {item.value for item in Webhook.Status}
    assert (
        str(exc_info.value)
        == f"Value `invalid..` does not exist in supported values. Expected one of {valid_webhook_statuses}"
    )

    with pytest.raises(ValueError) as exc_info:
        webhook.update(topics=["invalid.."])
    valid_webhook_topics = {item.value for item in Webhook.Topic}
    assert (
        str(exc_info.value)
        == f"Value `invalid..` does not exist in supported values. Expected one of {valid_webhook_topics}"
    )

    with pytest.raises(TypeError) as exc_info:
        webhook.update(topics="invalid..")
    assert (
        str(exc_info.value)
        == "Topics must be List[Webhook.Topic]. Found `invalid..`"
    )

    webhook.delete()


def test_webhook_create_with_no_secret(project, rand_gen):
    client = project.client
    secret = ""
    url = "https:/" + rand_gen(str)
    topics = []

    with pytest.raises(ValueError) as exc_info:
        Webhook.create(client, topics, url, secret, project)
    assert str(exc_info.value) == "Secret must be a non-empty string."


def test_webhook_create_with_no_topics(project, rand_gen):
    client = project.client
    secret = rand_gen(str)
    url = "https:/" + rand_gen(str)
    topics = []

    with pytest.raises(ValueError) as exc_info:
        Webhook.create(client, topics, url, secret, project)
    assert str(exc_info.value) == "Topics must be a non-empty list."


def test_webhook_create_with_no_url(project, rand_gen):
    client = project.client
    secret = rand_gen(str)
    url = ""
    topics = [Webhook.LABEL_CREATED, Webhook.LABEL_DELETED]

    with pytest.raises(ValueError) as exc_info:
        Webhook.create(client, topics, url, secret, project)
    assert str(exc_info.value) == "URL must be a non-empty string."
