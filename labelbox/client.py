# type: ignore
from datetime import datetime, timezone
import json

import logging
import mimetypes
import os

from google.api_core import retry
import requests
import requests.exceptions

import labelbox.exceptions
from labelbox import utils
from labelbox import __version__ as SDK_VERSION
from labelbox.orm import query
from labelbox.orm.db_object import DbObject
from labelbox.pagination import PaginatedCollection
from labelbox.schema.project import Project
from labelbox.schema.dataset import Dataset
from labelbox.schema.data_row import DataRow
from labelbox.schema.model import Model
from labelbox.schema.user import User
from labelbox.schema.organization import Organization
from labelbox.schema.data_row_metadata import DataRowMetadataOntology
from labelbox.schema.labeling_frontend import LabelingFrontend
from labelbox.schema.iam_integration import IAMIntegration
from labelbox.schema import role

logger = logging.getLogger(__name__)

_LABELBOX_API_KEY = "LABELBOX_API_KEY"


class Client:
    """ A Labelbox client.

    Contains info necessary for connecting to a Labelbox server (URL,
    authentication key). Provides functions for querying and creating
    top-level data objects (Projects, Datasets).
    """

    def __init__(self,
                 api_key=None,
                 endpoint='https://api.labelbox.com/graphql',
                 enable_experimental=False,
                 app_url="https://app.labelbox.com"):
        """ Creates and initializes a Labelbox Client.

        Logging is defaulted to level WARNING. To receive more verbose
        output to console, update `logging.level` to the appropriate level.

        >>> logging.basicConfig(level = logging.INFO)
        >>> client = Client("<APIKEY>")

        Args:
            api_key (str): API key. If None, the key is obtained from the "LABELBOX_API_KEY" environment variable.
            endpoint (str): URL of the Labelbox server to connect to.
            enable_experimental (bool): Indicates whether or not to use experimental features
            app_url (str) : host url for all links to the web app
        Raises:
            labelbox.exceptions.AuthenticationError: If no `api_key`
                is provided as an argument or via the environment
                variable.
        """
        if api_key is None:
            if _LABELBOX_API_KEY not in os.environ:
                raise labelbox.exceptions.AuthenticationError(
                    "Labelbox API key not provided")
            api_key = os.environ[_LABELBOX_API_KEY]
        self.api_key = api_key

        self.enable_experimental = enable_experimental
        if enable_experimental:
            logger.info("Experimental features have been enabled")

        logger.info("Initializing Labelbox client at '%s'", endpoint)
        self.app_url = app_url

        # TODO: Make endpoints non-internal or support them as experimental
        self.endpoint = endpoint.replace('/graphql', '/_gql')
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % api_key,
            'X-User-Agent': f'python-sdk {SDK_VERSION}'
        }

    @retry.Retry(predicate=retry.if_exception_type(
        labelbox.exceptions.InternalServerError))
    def execute(self,
                query=None,
                params=None,
                data=None,
                files=None,
                timeout=30.0,
                experimental=False):
        """ Sends a request to the server for the execution of the
        given query.

        Checks the response for errors and wraps errors
        in appropriate `labelbox.exceptions.LabelboxError` subtypes.

        Args:
            query (str): The query to execute.
            params (dict): Query parameters referenced within the query.
            data (str): json string containing the query to execute
            files (dict): file arguments for request
            timeout (float): Max allowed time for query execution,
                in seconds.
        Returns:
            dict, parsed JSON response.
        Raises:
            labelbox.exceptions.AuthenticationError: If authentication
                failed.
            labelbox.exceptions.InvalidQueryError: If `query` is not
                syntactically or semantically valid (checked server-side).
            labelbox.exceptions.ApiLimitError: If the server API limit was
                exceeded. See "How to import data" in the online documentation
                to see API limits.
            labelbox.exceptions.TimeoutError: If response was not received
                in `timeout` seconds.
            labelbox.exceptions.NetworkError: If an unknown error occurred
                most likely due to connection issues.
            labelbox.exceptions.LabelboxError: If an unknown error of any
                kind occurred.
            ValueError: If query and data are both None.
        """
        logger.debug("Query: %s, params: %r, data %r", query, params, data)

        # Convert datetimes to UTC strings.
        def convert_value(value):
            if isinstance(value, datetime):
                value = value.astimezone(timezone.utc)
                value = value.strftime("%Y-%m-%dT%H:%M:%SZ")
            return value

        if query is not None:
            if params is not None:
                params = {
                    key: convert_value(value) for key, value in params.items()
                }
            data = json.dumps({
                'query': query,
                'variables': params
            }).encode('utf-8')
        elif data is None:
            raise ValueError("query and data cannot both be none")
        try:
            request = {
                'url': self.endpoint,
                'data': data,
                'headers': self.headers,
                'timeout': timeout
            }
            if files:
                request.update({'files': files})
                request['headers'] = {
                    'Authorization': self.headers['Authorization']
                }

            response = requests.post(**request)
            logger.debug("Response: %s", response.text)
        except requests.exceptions.Timeout as e:
            raise labelbox.exceptions.TimeoutError(str(e))
        except requests.exceptions.RequestException as e:
            logger.error("Unknown error: %s", str(e))
            raise labelbox.exceptions.NetworkError(e)
        except Exception as e:
            raise labelbox.exceptions.LabelboxError(
                "Unknown error during Client.query(): " + str(e), e)
        try:
            r_json = response.json()
        except:
            if "upstream connect error or disconnect/reset before headers" \
                    in response.text:
                raise labelbox.exceptions.InternalServerError(
                    "Connection reset")
            elif response.status_code == 502:
                error_502 = '502 Bad Gateway'
                raise labelbox.exceptions.InternalServerError(error_502)

            raise labelbox.exceptions.LabelboxError(
                "Failed to parse response as JSON: %s" % response.text)

        errors = r_json.get("errors", [])

        def check_errors(keywords, *path):
            """ Helper that looks for any of the given `keywords` in any of
            current errors on paths (like error[path][component][to][keyword]).
            """
            for error in errors:
                obj = error
                for path_elem in path:
                    obj = obj.get(path_elem, {})
                if obj in keywords:
                    return error
            return None

        def get_error_status_code(error):
            return error["extensions"]["exception"]["status"]

        if check_errors(["AUTHENTICATION_ERROR"], "extensions",
                        "code") is not None:
            raise labelbox.exceptions.AuthenticationError("Invalid API key")

        authorization_error = check_errors(["AUTHORIZATION_ERROR"],
                                           "extensions", "code")
        if authorization_error is not None:
            raise labelbox.exceptions.AuthorizationError(
                authorization_error["message"])

        validation_error = check_errors(["GRAPHQL_VALIDATION_FAILED"],
                                        "extensions", "code")

        if validation_error is not None:
            message = validation_error["message"]
            if message == "Query complexity limit exceeded":
                raise labelbox.exceptions.ValidationFailedError(message)
            else:
                raise labelbox.exceptions.InvalidQueryError(message)

        graphql_error = check_errors(["GRAPHQL_PARSE_FAILED"], "extensions",
                                     "code")
        if graphql_error is not None:
            raise labelbox.exceptions.InvalidQueryError(
                graphql_error["message"])

        # Check if API limit was exceeded
        response_msg = r_json.get("message", "")

        if response_msg.startswith("You have exceeded"):
            raise labelbox.exceptions.ApiLimitError(response_msg)

        resource_not_found_error = check_errors(["RESOURCE_NOT_FOUND"],
                                                "extensions", "code")
        if resource_not_found_error is not None:
            # Return None and let the caller methods raise an exception
            # as they already know which resource type and ID was requested
            return None

        # A lot of different error situations are now labeled serverside
        # as INTERNAL_SERVER_ERROR, when they are actually client errors.
        # TODO: fix this in the server API
        internal_server_error = check_errors(["INTERNAL_SERVER_ERROR"],
                                             "extensions", "code")
        if internal_server_error is not None:
            message = internal_server_error.get("message")

            if get_error_status_code(internal_server_error) == 400:
                raise labelbox.exceptions.InvalidQueryError(message)
            else:
                raise labelbox.exceptions.InternalServerError(message)

        if len(errors) > 0:
            logger.warning("Unparsed errors on query execution: %r", errors)
            raise labelbox.exceptions.LabelboxError("Unknown error: %s" %
                                                    str(errors))

        # if we do return a proper error code, and didn't catch this above
        # reraise
        # this mainly catches a 401 for API access disabled for free tier
        # TODO: need to unify API errors to handle things more uniformly
        # in the SDK
        if response.status_code != requests.codes.ok:
            message = f"{response.status_code} {response.reason}"
            cause = r_json.get('message')
            raise labelbox.exceptions.LabelboxError(message, cause)

        return r_json["data"]

    def upload_file(self, path: str) -> str:
        """Uploads given path to local file.

        Also includes best guess at the content type of the file.

        Args:
            path (str): path to local file to be uploaded.
        Returns:
            str, the URL of uploaded data.
        Raises:
            labelbox.exceptions.LabelboxError: If upload failed.
        """
        content_type, _ = mimetypes.guess_type(path)
        filename = os.path.basename(path)
        with open(path, "rb") as f:
            return self.upload_data(content=f.read(),
                                    filename=filename,
                                    content_type=content_type)

    @retry.Retry(predicate=retry.if_exception_type(
        labelbox.exceptions.InternalServerError))
    def upload_data(self,
                    content: bytes,
                    filename: str = None,
                    content_type: str = None,
                    sign: bool = False) -> str:
        """ Uploads the given data (bytes) to Labelbox.

        Args:
            content: bytestring to upload
            filename: name of the upload
            content_type: content type of data uploaded
            sign: whether or not to sign the url

        Returns:
            str, the URL of uploaded data.

        Raises:
            labelbox.exceptions.LabelboxError: If upload failed.
        """

        request_data = {
            "operations":
                json.dumps({
                    "variables": {
                        "file": None,
                        "contentLength": len(content),
                        "sign": sign
                    },
                    "query":
                        """mutation UploadFile($file: Upload!, $contentLength: Int!,
                                            $sign: Boolean) {
                            uploadFile(file: $file, contentLength: $contentLength,
                                       sign: $sign) {url filename} } """,
                }),
            "map": (None, json.dumps({"1": ["variables.file"]})),
        }
        response = requests.post(
            self.endpoint,
            headers={"authorization": "Bearer %s" % self.api_key},
            data=request_data,
            files={
                "1": (filename, content, content_type) if
                     (filename and content_type) else content
            })

        if response.status_code == 502:
            error_502 = '502 Bad Gateway'
            raise labelbox.exceptions.InternalServerError(error_502)
        elif response.status_code == 503:
            raise labelbox.exceptions.InternalServerError(response.text)

        try:
            file_data = response.json().get("data", None)
        except ValueError as e:  # response is not valid JSON
            raise labelbox.exceptions.LabelboxError(
                "Failed to upload, unknown cause", e)

        if not file_data or not file_data.get("uploadFile", None):
            raise labelbox.exceptions.LabelboxError(
                "Failed to upload, message: %s" % file_data.get("error", None))

        return file_data["uploadFile"]["url"]

    def _get_single(self, db_object_type, uid):
        """ Fetches a single object of the given type, for the given ID.

        Args:
            db_object_type (type): DbObject subclass.
            uid (str): Unique ID of the row.
        Returns:
            Object of `db_object_type`.
        Raises:
            labelbox.exceptions.ResourceNotFoundError: If there is no object
                of the given type for the given ID.
        """
        query_str, params = query.get_single(db_object_type, uid)
        res = self.execute(query_str, params)
        res = res and res.get(utils.camel_case(db_object_type.type_name()))
        if res is None:
            raise labelbox.exceptions.ResourceNotFoundError(
                db_object_type, params)
        else:
            return db_object_type(self, res)

    def get_project(self, project_id):
        """ Gets a single Project with the given ID.

            >>> project = client.get_project("<project_id>")

        Args:
            project_id (str): Unique ID of the Project.
        Returns:
            The sought Project.
        Raises:
            labelbox.exceptions.ResourceNotFoundError: If there is no
                Project with the given ID.
        """
        return self._get_single(Project, project_id)

    def get_dataset(self, dataset_id):
        """ Gets a single Dataset with the given ID.

            >>> dataset = client.get_dataset("<dataset_id>")

        Args:
            dataset_id (str): Unique ID of the Dataset.
        Returns:
            The sought Dataset.
        Raises:
            labelbox.exceptions.ResourceNotFoundError: If there is no
                Dataset with the given ID.
        """
        return self._get_single(Dataset, dataset_id)

    def get_user(self):
        """ Gets the current User database object.

            >>> user = client.get_user()
        """
        return self._get_single(User, None)

    def get_organization(self):
        """ Gets the Organization DB object of the current user.

            >>> organization = client.get_organization()

        """
        return self._get_single(Organization, None)

    def _get_all(self, db_object_type, where, filter_deleted=True):
        """ Fetches all the objects of the given type the user has access to.

        Args:
            db_object_type (type): DbObject subclass.
            where (Comparison, LogicalOperation or None): The `where` clause
                for filtering.
        Returns:
            An iterable of `db_object_type` instances.
        """
        if filter_deleted:
            not_deleted = db_object_type.deleted == False
            where = not_deleted if where is None else where & not_deleted
        query_str, params = query.get_all(db_object_type, where)

        return PaginatedCollection(
            self, query_str, params,
            [utils.camel_case(db_object_type.type_name()) + "s"],
            db_object_type)

    def get_projects(self, where=None):
        """ Fetches all the projects the user has access to.

            >>> projects = client.get_projects(where=(Project.name == "<project_name>") & (Project.description == "<project_description>"))

        Args:
            where (Comparison, LogicalOperation or None): The `where` clause
                for filtering.
        Returns:
            An iterable of Projects (typically a PaginatedCollection).
        """
        return self._get_all(Project, where)

    def get_datasets(self, where=None):
        """ Fetches one or more datasets.

            >>> datasets = client.get_datasets(where=(Dataset.name == "<dataset_name>") & (Dataset.description == "<dataset_description>"))

        Args:
            where (Comparison, LogicalOperation or None): The `where` clause
                for filtering.
        Returns:
            An iterable of Datasets (typically a PaginatedCollection).
        """
        return self._get_all(Dataset, where)

    def get_labeling_frontends(self, where=None):
        """ Fetches all the labeling frontends.

            >>> frontend = client.get_labeling_frontends(where=LabelingFrontend.name == "Editor")

        Args:
            where (Comparison, LogicalOperation or None): The `where` clause
                for filtering.
        Returns:
            An iterable of LabelingFrontends (typically a PaginatedCollection).
        """
        return self._get_all(LabelingFrontend, where)

    def _create(self, db_object_type, data):
        """ Creates an object on the server. Attribute values are
            passed as keyword arguments:

        Args:
            db_object_type (type): A DbObjectType subtype.
            data (dict): Keys are attributes or their names (in Python,
                snake-case convention) and values are desired attribute values.
        Returns:
            A new object of the given DB object type.
        Raises:
            InvalidAttributeError: If the DB object type does not contain
                any of the attribute names given in `data`.
        """
        # Convert string attribute names to Field or Relationship objects.
        # Also convert Labelbox object values to their UIDs.
        data = {
            db_object_type.attribute(attr) if isinstance(attr, str) else attr:
            value.uid if isinstance(value, DbObject) else value
            for attr, value in data.items()
        }

        query_string, params = query.create(db_object_type, data)
        res = self.execute(query_string, params)
        res = res["create%s" % db_object_type.type_name()]
        return db_object_type(self, res)

    def create_dataset(self, iam_integration=IAMIntegration._DEFAULT, **kwargs):
        """ Creates a Dataset object on the server.

        Attribute values are passed as keyword arguments.

        >>> project = client.get_project("<project_uid>")
        >>> dataset = client.create_dataset(name="<dataset_name>", projects=project)

        Args:
            iam_integration (IAMIntegration) : Uses the default integration.
                Optionally specify another integration or set as None to not use delegated access
            **kwargs: Keyword arguments with Dataset attribute values.
        Returns:
            A new Dataset object.
        Raises:
            InvalidAttributeError: If the Dataset type does not contain
                any of the attribute names given in kwargs.
        """
        dataset = self._create(Dataset, kwargs)

        if iam_integration == IAMIntegration._DEFAULT:
            iam_integration = self.get_organization(
            ).get_default_iam_integration()

        if iam_integration is None:
            return dataset

        if not isinstance(iam_integration, IAMIntegration):
            raise TypeError(
                f"iam integration must be a reference an `IAMIntegration` object. Found {type(iam_integration)}"
            )

        if not iam_integration.valid:
            raise ValueError("Integration is not valid. Please select another.")

        try:
            self.execute(
                """mutation setSignerForDatasetPyApi($signerId: ID!, $datasetId: ID!) {
                    setSignerForDataset(data: { signerId: $signerId}, where: {id: $datasetId}){id}}
                """, {
                    'signerId': iam_integration.uid,
                    'datasetId': dataset.uid
                })
            validation_result = self.execute(
                """mutation validateDatasetPyApi($id: ID!){validateDataset(where: {id : $id}){
                    valid checks{name, success}}}
                """, {'id': dataset.uid})

            if not validation_result['validateDataset']['valid']:
                raise labelbox.exceptions.LabelboxError(
                    f"IAMIntegration was not successfully added to the dataset."
                )
        except Exception as e:
            dataset.delete()
            raise e
        return dataset

    def create_project(self, **kwargs):
        """ Creates a Project object on the server.

        Attribute values are passed as keyword arguments.

        >>> project = client.create_project(name="<project_name>", description="<project_description>")

        Args:
            **kwargs: Keyword arguments with Project attribute values.
        Returns:
            A new Project object.
        Raises:
            InvalidAttributeError: If the Project type does not contain
                any of the attribute names given in kwargs.
        """
        return self._create(Project, kwargs)

    def get_roles(self):
        """
        Returns:
            Roles: Provides information on available roles within an organization.
            Roles are used for user management.
        """
        return role.get_roles(self)

    def get_data_row(self, data_row_id):
        """

        Returns:
            DataRow: returns a single data row given the data row id
        """

        return self._get_single(DataRow, data_row_id)

    def get_data_row_metadata_ontology(self):
        """

        Returns:
            DataRowMetadataOntology: The ontology for Data Row Metadata for an organization

        """
        return DataRowMetadataOntology(self)

    def get_model(self, model_id):
        """ Gets a single Model with the given ID.

            >>> model = client.get_model("<model_id>")

        Args:
            model_id (str): Unique ID of the Model.
        Returns:
            The sought Model.
        Raises:
            labelbox.exceptions.ResourceNotFoundError: If there is no
                Model with the given ID.
        """
        return self._get_single(Model, model_id)

    def get_models(self, where=None):
        """ Fetches all the models the user has access to.

            >>> models = client.get_models(where=(Model.name == "<model_name>"))

        Args:
            where (Comparison, LogicalOperation or None): The `where` clause
                for filtering.
        Returns:
            An iterable of Models (typically a PaginatedCollection).
        """
        return self._get_all(Model, where, filter_deleted=False)

    def create_model(self, name, ontology_id):
        """ Creates a Model object on the server.

        >>> model = client.create_model(<model_name>, <ontology_id>)

        Args:
            name (string): Name of the model
            ontology_id (string): ID of the related ontology
        Returns:
            A new Model object.
        Raises:
            InvalidAttributeError: If the Model type does not contain
                any of the attribute names given in kwargs.
        """
        query_str = """mutation createModelPyApi($name: String!, $ontologyId: ID!){
            createModel(data: {name : $name, ontologyId : $ontologyId}){
                    %s
                }
            }""" % query.results_query_part(Model)

        result = self.execute(query_str, {
            "name": name,
            "ontologyId": ontology_id
        })
        return Model(self, result['createModel'])
