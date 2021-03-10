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
    assert str(exc_info.value) == \
        f"Value `invalid..` does not exist in supported values. Expected one of {[x.value for x in Webhook.WebhookStatus]}"

    with pytest.raises(ValueError) as exc_info:
        webhook.update(topics=["invalid.."])
    assert str(exc_info.value) == \
        f"Value `invalid..` does not exist in supported values. Expected one of {[x.value for x in Webhook.WebhookTopic]}"

    with pytest.raises(TypeError) as exc_info:
        webhook.update(topics="invalid..")
    assert str(exc_info.value) == \
        "Topics must be List[Webhook.WebhookTopic]. Found `invalid..`"
