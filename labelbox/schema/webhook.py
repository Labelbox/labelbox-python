from labelbox.orm import query
from labelbox.orm.db_object import DbObject, Updateable
from labelbox.orm.model import Entity, Field, Relationship


class Webhook(DbObject, Updateable):
    """ Represents a server-side rule for sending notifications to a web-server
    whenever one of several predefined actions happens within a context of
    a Project or an Organization.
    """

    # Status
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    REVOKED = "REVOKED"

    # Topic
    LABEL_CREATED = "LABEL_CREATED"
    LABEL_UPDATED = "LABEL_UPDATED"
    LABEL_DELETED = "LABEL_DELETED"

    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    url = Field.String("url")
    topics = Field.String("topics")
    status = Field.String("status")

    @staticmethod
    def create(client, topics, url, secret, project):
        """ Creates a Webhook.

        Args:
            client (Client): The Labelbox client used to connect
                to the server.
            topics (list of str): A list of topics this Webhook should
                get notifications for.
            url (str): The URL to which notifications should be sent
                by the Labelbox server.
            secret (str): A secret key used for signing notifications.
            project (Project or None): The project for which notifications
                should be sent. If None notifications are sent for all
                events in your organization.
        Returns:
            A newly created Webhook.
        """
        project_str = "" if project is None \
            else ("project:{id:\"%s\"}," % project.uid)

        query_str = """mutation CreateWebhookPyApi {
            createWebhook(data:{%s topics:{set:[%s]}, url:"%s", secret:"%s" }){%s}
        } """ % (project_str, " ".join(topics), url, secret,
                 query.results_query_part(Entity.Webhook))

        return Webhook(client, client.execute(query_str)["createWebhook"])

    created_by = Relationship.ToOne("User", False, "created_by")
    organization = Relationship.ToOne("Organization")
    project = Relationship.ToOne("Project")

    def update(self, topics=None, url=None, status=None):
        """ Updates this Webhook.
        
        Args:
            topics (list of str): The new topics value, optional.
            url (str): The new URL value, optional.
            status (str): The new status value, optional.
        """
        # Webhook has a custom `update` function due to custom types
        # in `status` and `topics` fields.
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
