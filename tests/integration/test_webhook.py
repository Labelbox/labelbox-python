from threading import Thread
import time

from labelbox import Webhook


def test_webhook_create_update(client, rand_gen):

    project = client.create_project(name=rand_gen(str))
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

    project.delete()
