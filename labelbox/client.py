import json
import logging
import os
import urllib.request

import requests

from labelbox import query, utils
from labelbox.exceptions import (NetworkError, AuthenticationError,
                                 ResourceNotFoundError, LabelboxError)
from labelbox.db_objects import Project, Dataset, User


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
        self.api_key = api_key

        logging.info("Initializing Labelbox client at '%s'", endpoint)

        self.endpoint = endpoint
        self.headers = {'Accept': 'application/json',
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer %s' % api_key}

    def execute(self, query, params=None):
        """ Execute a GraphQL query on the server.

        Args:
            query (str): the query to execute.
            params (dict): query parameters referenced within the query.
        Return:
            dict, parsed JSON response.
        Raises:
            labelbox.exception.NetworkError: If an urllib.error.HTTPError
                occurred.
            labelbox.exception.AuthenticationError: If authentication
                failed.
        """
        logger.debug("Query: %s, params: %r", query, params)
        data = json.dumps(
            {'query': query, 'variables': params}).encode('utf-8')
        req = urllib.request.Request(self.endpoint, data, self.headers)

        try:
            response = urllib.request.urlopen(req)
            return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            # Convert HTTPError into a Labelbox error
            raise NetworkError(e)

    def upload_data(self, data):
        """ Uploads the given data (bytes) to Labelbox.
        Args:
            data (bytes): the data to upload.
        Return:
            str, the URL of uploaded data.
        Raises:
            LabelboxError: if upload failes.
        """
        request_data = {
            "operations": json.dumps({
            "variables": {"file": None, "contentLength": len(data), "sign": False},
            "query": """mutation UploadFile($file: Upload!, $contentLength: Int!,
                                            $sign: Boolean) {
                            uploadFile(file: $file, contentLength: $contentLength,
                                       sign: $sign) {url filename} } """,}),
            "map": (None, json.dumps({"1": ["variables.file"]})),
            }
        request = requests.post(
            self.endpoint,
            headers={"authorization": "Bearer %s" % self.api_key},
            data=request_data,
            files={"1": data}
        )

        try:
            file_data = request.json().get("data", None)
        except ValueError: # response is not valid JSON
            raise LabelboxError("Failed to upload, unknown cause")

        if not file_data or not file_data.get("uploadFile", None):
            raise LabelboxError("Failed to upload, message: %s" % file_data.get(
                "error", None))

        return file_data["uploadFile"]["url"]

    def get_single(self, db_object_type, uid):
        """ Fetches a single object of the given type, for the given ID.

        Args:
            db_object_type (type): DbObject subclass.
            uid (str): Unique ID of the row.
        Return:
            Object of `db_object_type`.
        Raises:
            labelbox.exception.ResourceNotFoundError: If there is no object
                of the given type for the given ID.
            labelbox.exception.LabelboxError: Any error raised by
                `Client.execute` can also be raised by this function.
        """
        query_str, id_param_name = query.get_single(db_object_type)
        params = {id_param_name: uid}
        res = self.execute(query_str, params)["data"][
            utils.camel_case(db_object_type.type_name())]
        if res is None:
            raise ResourceNotFoundError(db_object_type, params)
        else:
            return db_object_type(self, res)

    def get_project(self, project_id):
        """ Convenience for `client.get_single(Project, project_id)`. """
        return self.get_single(Project, project_id)

    def get_dataset(self, dataset_id):
        """ Convenience for `client.get_single(Dataset, dataset_id)`. """
        return self.get_single(Dataset, dataset_id)

    def get_user(self):
        """ Gets the current user database object. """
        res = self.execute(query.get_user(User))["data"][
            utils.camel_case(User.type_name())]
        return User(self, res)

    def get_all(self, db_object_type, where):
        """ Fetches all the objects of the given type the user has access to.

        Args:
            db_object_type (type): DbObject subclass.
            where (Comparison, LogicalOperation or None): The `where` clause
                for filtering.
        Return:
            An iterable of `db_object_type` instances.
        Raises:
            labelbox.exception.LabelboxError: Any error raised by
                `Client.execute` can also be raised by this function.
        """
        not_deleted = db_object_type.deleted == False
        where = not_deleted if where is None else where & not_deleted
        query_str, params = query.get_all(db_object_type, where)
        return query.PaginatedCollection(
            self, query_str, params,
            [utils.camel_case(db_object_type.type_name()) + "s"],
            db_object_type)

    def get_projects(self, where=None):
        """ Fetches all the projects the user has access to.

        Args:
            where (Comparison, LogicalOperation or None): The `where` clause
                for filtering.
        Return:
            An iterable of Projects (typically a PaginatedCollection).
        Raises:
            labelbox.exception.LabelboxError: Any error raised by
                `Client.execute` can also be raised by this function.
        """
        return self.get_all(Project, where)

    def get_datasets(self, where=None):
        """ Fetches all the datasets the user has access to.

        Args:
            where (Comparison, LogicalOperation or None): The `where` clause
                for filtering.
        Return:
            An iterable of Datasets (typically a PaginatedCollection).
        Raises:
            labelbox.exception.LabelboxError: Any error raised by
                `Client.execute` can also be raised by this function.
        """
        return self.get_all(Dataset, where)

    def create(self, db_object_type, data):
        """ Creates a object on the server. Attribute values are
            passed as keyword arguments:
                >>> project = client.create(Project, name="MyDataset")

        Args:
            db_object_type (type): A DbObjectType subtype.
            **data (dict): keyword arguments with new object attribute values.
                Keys are field names (in Python, snake-case convention) and
                values are desired attribute values.
        Return:
            a new object of the given DB object type.
        Raises:
            InvalidFieldError: in case the DB object type does not contain
                any of the field names given in `data`.
        """
        data = {db_object_type.field(name): value
                for name, value in data.items()}

        query_string, params = query.create(db_object_type, data)
        res = self.execute(query_string, params)
        res = res["data"]["create%s" % db_object_type.type_name()]
        return db_object_type(self, res)

    def create_dataset(self, **data):
        """ Creates a Dataset object on the server. Attribute values are
            passed as keyword arguments:
                >>> dataset = client.create_dataset(name="MyDataset")

        Args:
            **data (dict): keyword arguments with new Dataset attribute values.
                Keys are field names (in Python, snake-case convention) and
                values are desired attribute values.
        Return:
            a new Dataset object.
        Raises:
            InvalidFieldError: in case the Dataset type does not contain
                any of the field names given in `data`.
        """
        return self.create(Dataset, data)

    def create_project(self, **data):
        """ Creates a Project object on the server. Attribute values are
            passed as keyword arguments:
                >>> project = client.create_project(name="MyProject")

        Args:
            **data (dict): keyword arguments with new Project attribute values.
                Keys are field names (in Python, snake-case convention) and
                values are desired attribute values.
        Return:
            a new Project object.
        Raises:
            InvalidFieldError: in case the Project type does not contain
                any of the field names given in `data`.
        """
        return self.create(Project, data)
