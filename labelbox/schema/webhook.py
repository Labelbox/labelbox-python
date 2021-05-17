import logging
from enum import Enum
from typing import Iterable, List

from labelbox.orm import query
from labelbox.orm.db_object import DbObject, Updateable
from labelbox.orm.model import Entity, Field, Relationship

logger = logging.getLogger(__name__)


class Webhook(DbObject, Updateable):
    """ Represents a server-side rule for sending notifications to a web-server
    whenever one of several predefined actions happens within a context of
    a Project or an Organization.

    Attributes:
        updated_at (datetime)
        created_at (datetime)
        url (str)
        topics (str): LABEL_CREATED, LABEL_UPDATED, LABEL_DELETED
            REVIEW_CREATED, REVIEW_UPDATED, REVIEW_DELETED
        status (str): ACTIVE, INACTIVE, REVOKED

    """

    class Status(Enum):
        ACTIVE = "ACTIVE"
        INACTIVE = "INACTIVE"
        REVOKED = "REVOKED"

    class Topic(Enum):
        LABEL_CREATED = "LABEL_CREATED"
        LABEL_UPDATED = "LABEL_UPDATED"
        LABEL_DELETED = "LABEL_DELETED"
        REVIEW_CREATED = "REVIEW_CREATED"
        REVIEW_UPDATED = "REVIEW_UPDATED"
        REVIEW_DELETED = "REVIEW_DELETED"

    # For backwards compatibility
    for topic in Status:
        vars()[topic.name] = topic.value

    for status in Topic:
        vars()[status.name] = status.value

    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    url = Field.String("url")
    topics = Field.String("topics")
    status = Field.String("status")

    created_by = Relationship.ToOne("User", False, "created_by")
    organization = Relationship.ToOne("Organization")
    project = Relationship.ToOne("Project")

    @staticmethod
    def create(client, topics, url, secret, project):
        """ Creates a Webhook.

        Args:
            client (Client): The Labelbox client used to connect
                to the server.
            topics (list of str): A list of topics this Webhook should
                get notifications for. Must be one of Webhook.Topic
            url (str): The URL to which notifications should be sent
                by the Labelbox server.
            secret (str): A secret key used for signing notifications.
            project (Project or None): The project for which notifications
                should be sent. If None notifications are sent for all
                events in your organization.
        Returns:
            A newly created Webhook.

        Raises:
            ValueError: If the topic is not one of Topic or status is not one of Status

        Information on configuring your server can be found here (this is where the url points to and the secret is set).
                        https://docs.labelbox.com/en/configure-editor/webhooks-setup#setup-steps

        """
        Webhook.validate_topics(topics)

        project_str = "" if project is None \
            else ("project:{id:\"%s\"}," % project.uid)

        query_str = """mutation CreateWebhookPyApi {
            createWebhook(data:{%s topics:{set:[%s]}, url:"%s", secret:"%s" }){%s}
        } """ % (project_str, " ".join(topics), url, secret,
                 query.results_query_part(Entity.Webhook))

        return Webhook(client, client.execute(query_str)["createWebhook"])

    @staticmethod
    def validate_topics(topics):
        if isinstance(topics, str) or not isinstance(topics, Iterable):
            raise TypeError(
                f"Topics must be List[Webhook.Topic]. Found `{topics}`")

        for topic in topics:
            Webhook.validate_value(topic, Webhook.Topic)

    @staticmethod
    def validate_value(value, enum):
        supported_values = {item.value for item in enum}
        if value not in supported_values:
            raise ValueError(
                f"Value `{value}` does not exist in supported values. Expected one of {supported_values}"
            )

    def delete(self):
        """
        Deletes the webhook
        """
        self.update(status=self.Status.INACTIVE.value)

    def update(self, topics=None, url=None, status=None):
        """ Updates the Webhook.

        Args:
            topics (Optional[List[Topic]]): The new topics.
            url  Optional[str): The new URL value.
            status (Optional[Status]): The new status.
                If an argument is set to None then no updates will be made to that field.

        """

        # Webhook has a custom `update` function due to custom types
        # in `status` and `topics` fields.

        if topics is not None:
            self.validate_topics(topics)

        if status is not None:
            self.validate_value(status, self.Status)

        topics_str = "" if topics is None \
            else "topics: {set: [%s]}" % " ".join(topics)
        url_str = "" if url is None else "url: \"%s\"" % url
        status_str = "" if status is None else "status: %s" % status

        query_str = """mutation UpdateWebhookPyApi {
            updateWebhook(where: {id: "%s"} data:{%s}){%s}} """ % (
            self.uid, ", ".join(filter(None,
                                       (topics_str, url_str, status_str))),
            query.results_query_part(Entity.Webhook))

        self._set_field_values(self.client.execute(query_str)["updateWebhook"])
