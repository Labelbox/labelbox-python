import json
import logging
import os
import urllib.request

from labelbox.exceptions import (NetworkError, AuthenticationError,
                                 ResourceNotFoundError)
from labelbox.db_objects import Project
from labelbox.query import PaginatedCollection


logger = logging.getLogger(__name__)


class Client:
    """ A Labelbox client. Containes info necessary for connecting to
    the server (URL, authentication key). Provides functions for querying
    and creating top-level data objects (Projects, Datasets).
    """

    def __init__(self, api_key=None,
                 endpoint='https://api.labelbox.com/graphql'):
        """ Create and initialize a Labelbox Client.

        Args:
            api_key (str): API key. If None, the key is obtained from
                the "LABELBOX_API_KEY" environment variable.
            endpoint (str): URL of the Labelbox server to connect to.
        """
        if api_key is None:
            api_key = os.environ["LABELBOX_API_KEY"]

        self.endpoint = endpoint
        self.headers = {'Accept': 'application/json',
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer %s' % api_key}

    def execute(self, query, variables=None):
        """ Execute a GraphQL query on the server.

        Args:
            query: str, the query to execute.
            variables: dict, variables referenced within the query.
        Return:
            dict, parsed JSON response.
        Raises:
            labelbox.exception.NetworkError: If an urllib.error.HTTPError
                occurred.
            labelbox.exception.AuthenticationError: If authentication
                failed.
        """
        logger.debug("Query: %s", query)
        data = json.dumps({'query': query, 'variables': variables}).encode('utf-8')
        req = urllib.request.Request(self.endpoint, data, self.headers)

        try:
            response = urllib.request.urlopen(req)
            return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            # Convert HTTPError into a Labelbox error
            raise NetworkError(e)

    def get_project(self, project_id):
        """ Fetches the project for the given ID.

        Args:
            project_id (str): Unique ID of the project.
        Return:
            Project object.
        Raises:
            labelbox.exception.ResourceNotFoundError: If there is no Project
                for the given ID.
            labelbox.exception.LabelboxError: Any error raised by
                `Client.execute` can also be raised by this function.
        """
        fields = " ".join(field.graphql_name for field in Project.fields())
        query = "query GetProjectPyApi {project(where: {id: \"%s\"}) {%s} }" % (
            project_id, fields)
        res = self.execute(query)
        # TODO check if result contains Project data, if not raise
        # ResourceNotFoundError
        return Project(self, res["data"]["project"])

    def get_projects(self):
        """ Fetches all the projects the user has access to.

        Return:
            An iterable of Projects (typically a PaginatedCollection).
        Raises:
            labelbox.exception.LabelboxError: Any error raised by
                `Client.execute` can also be raised by this function.
        """
        fields = " ".join(field.graphql_name for field in Project.fields())
        query = "query GetProjectsPyApi {projects(skip: %%d first: %%d) {%s} }" \
            % fields
        return PaginatedCollection(self, query, ["projects"], Project)
