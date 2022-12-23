# type: ignore
from datetime import datetime, timezone
import json
from typing import Any, List, Dict, Union
from collections import defaultdict

import logging
import mimetypes
import os
import time

from google.api_core import retry
import requests
import requests.exceptions

import labelbox.exceptions
from labelbox import utils
from labelbox import __version__ as SDK_VERSION
from labelbox.orm import query
from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Entity
from labelbox.pagination import PaginatedCollection
from labelbox.schema.data_row_metadata import DataRowMetadataOntology
from labelbox.schema.dataset import Dataset
from labelbox.schema.enums import CollectionJobStatus
from labelbox.schema.iam_integration import IAMIntegration
from labelbox.schema import role
from labelbox.schema.labeling_frontend import LabelingFrontend
from labelbox.schema.model import Model
from labelbox.schema.model_run import ModelRun
from labelbox.schema.ontology import Ontology, Tool, Classification
from labelbox.schema.organization import Organization
from labelbox.schema.user import User
from labelbox.schema.project import Project
from labelbox.schema.role import Role
from labelbox.schema.slice import CatalogSlice
from labelbox.schema.queue_mode import QueueMode

from labelbox.schema.media_type import MediaType, get_media_type_validation_error

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
        self.endpoint = endpoint
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % api_key,
            'X-User-Agent': f'python-sdk {SDK_VERSION}'
        }
        self._data_row_metadata_ontology = None

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

        endpoint = self.endpoint if not experimental else self.endpoint.replace(
            "/graphql", "/_gql")
        try:
            request = {
                'url': endpoint,
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
            return error["extensions"].get("code")

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

        resource_conflict_error = check_errors(["RESOURCE_CONFLICT"],
                                               "extensions", "code")
        if resource_conflict_error is not None:
            raise labelbox.exceptions.ResourceConflict(
                resource_conflict_error["message"])

        malformed_request_error = check_errors(["MALFORMED_REQUEST"],
                                               "extensions", "code")
        if malformed_request_error is not None:
            raise labelbox.exceptions.MalformedQueryException(
                malformed_request_error["message"])

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

        not_allowed_error = check_errors(["OPERATION_NOT_ALLOWED"],
                                         "extensions", "code")
        if not_allowed_error is not None:
            message = not_allowed_error.get("message")
            raise labelbox.exceptions.OperationNotAllowedException(message)

        if len(errors) > 0:
            logger.warning("Unparsed errors on query execution: %r", errors)
            messages = list(
                map(
                    lambda x: {
                        "message": x["message"],
                        "code": x["extensions"]["code"]
                    }, errors))
            raise labelbox.exceptions.LabelboxError("Unknown error: %s" %
                                                    str(messages))

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
            try:
                errors = response.json().get("errors", [])
                error_msg = next(iter(errors), {}).get("message",
                                                       "Unknown error")
            except Exception as e:
                error_msg = "Unknown error"
            raise labelbox.exceptions.LabelboxError(
                "Failed to upload, message: %s" % error_msg)

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
        return self._get_single(Entity.Project, project_id)

    def get_dataset(self, dataset_id) -> Dataset:
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
        return self._get_single(Entity.Dataset, dataset_id)

    def get_user(self) -> User:
        """ Gets the current User database object.

            >>> user = client.get_user()
        """
        return self._get_single(Entity.User, None)

    def get_organization(self) -> Organization:
        """ Gets the Organization DB object of the current user.

            >>> organization = client.get_organization()

        """
        return self._get_single(Entity.Organization, None)

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

    def get_projects(self, where=None) -> List[Project]:
        """ Fetches all the projects the user has access to.

            >>> projects = client.get_projects(where=(Project.name == "<project_name>") & (Project.description == "<project_description>"))

        Args:
            where (Comparison, LogicalOperation or None): The `where` clause
                for filtering.
        Returns:
            An iterable of Projects (typically a PaginatedCollection).
        """
        return self._get_all(Entity.Project, where)

    def get_datasets(self, where=None) -> List[Dataset]:
        """ Fetches one or more datasets.

            >>> datasets = client.get_datasets(where=(Dataset.name == "<dataset_name>") & (Dataset.description == "<dataset_description>"))

        Args:
            where (Comparison, LogicalOperation or None): The `where` clause
                for filtering.
        Returns:
            An iterable of Datasets (typically a PaginatedCollection).
        """
        return self._get_all(Entity.Dataset, where)

    def get_labeling_frontends(self, where=None) -> List[LabelingFrontend]:
        """ Fetches all the labeling frontends.

            >>> frontend = client.get_labeling_frontends(where=LabelingFrontend.name == "Editor")

        Args:
            where (Comparison, LogicalOperation or None): The `where` clause
                for filtering.
        Returns:
            An iterable of LabelingFrontends (typically a PaginatedCollection).
        """
        return self._get_all(Entity.LabelingFrontend, where)

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

    def create_dataset(self,
                       iam_integration=IAMIntegration._DEFAULT,
                       **kwargs) -> Dataset:
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
        dataset = self._create(Entity.Dataset, kwargs)

        if iam_integration == IAMIntegration._DEFAULT:
            iam_integration = self.get_organization(
            ).get_default_iam_integration()

        if iam_integration is None:
            return dataset

        try:
            if not isinstance(iam_integration, IAMIntegration):
                raise TypeError(
                    f"iam integration must be a reference an `IAMIntegration` object. Found {type(iam_integration)}"
                )

            if not iam_integration.valid:
                raise ValueError(
                    "Integration is not valid. Please select another.")

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

    def create_project(self, **kwargs) -> Project:
        """ Creates a Project object on the server.

        Attribute values are passed as keyword arguments.

        >>> project = client.create_project(
                name="<project_name>",
                description="<project_description>",
                media_type=MediaType.Image,
                queue_mode=QueueMode.Batch
            )

        Args:
            name (str): A name for the project
            description (str): A short summary for the project
            media_type (MediaType): The type of assets that this project will accept
            queue_mode (Optional[QueueMode]): The queue mode to use
            auto_audit_percentage (Optional[float]): The percentage of data rows that will require more than 1 label
            auto_audit_number_of_labels (Optional[float]): Number of labels required for data rows selected for multiple labeling (auto_audit_percentage)
        Returns:
            A new Project object.
        Raises:
            InvalidAttributeError: If the Project type does not contain
                any of the attribute names given in kwargs.
        """
        media_type = kwargs.get("media_type")
        queue_mode = kwargs.get("queue_mode")
        if media_type:
            if MediaType.is_supported(media_type):
                media_type = media_type.value
            else:
                raise TypeError(f"{media_type} is not a valid media type. Use"
                                f" any of {MediaType.get_supported_members()}"
                                " from MediaType. Example: MediaType.Image.")
        else:
            logger.warning(
                "Creating a project without specifying media_type"
                " through this method will soon no longer be supported.")

        if not queue_mode:
            logger.warning(
                "Default createProject behavior will soon be adjusted to prefer "
                "batch projects. Pass in `queue_mode` parameter explicitly to opt-out for the "
                "time being.")
        elif queue_mode == QueueMode.Dataset:
            logger.warning(
                "QueueMode.Dataset will eventually be deprecated, and is no longer "
                "recommended for new projects. Prefer QueueMode.Batch instead.")

        return self._create(Entity.Project, {
            **kwargs,
            **({
                'media_type': media_type
            } if media_type else {})
        })

    def get_roles(self) -> List[Role]:
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

        return self._get_single(Entity.DataRow, data_row_id)

    def get_data_row_metadata_ontology(self) -> DataRowMetadataOntology:
        """

        Returns:
            DataRowMetadataOntology: The ontology for Data Row Metadata for an organization

        """
        if self._data_row_metadata_ontology is None:
            self._data_row_metadata_ontology = DataRowMetadataOntology(self)
        return self._data_row_metadata_ontology

    def get_model(self, model_id) -> Model:
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
        return self._get_single(Entity.Model, model_id)

    def get_models(self, where=None) -> List[Model]:
        """ Fetches all the models the user has access to.

            >>> models = client.get_models(where=(Model.name == "<model_name>"))

        Args:
            where (Comparison, LogicalOperation or None): The `where` clause
                for filtering.
        Returns:
            An iterable of Models (typically a PaginatedCollection).
        """
        return self._get_all(Entity.Model, where, filter_deleted=False)

    def create_model(self, name, ontology_id) -> Model:
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
            }""" % query.results_query_part(Entity.Model)

        result = self.execute(query_str, {
            "name": name,
            "ontologyId": ontology_id
        })
        return Entity.Model(self, result['createModel'])

    def get_data_row_ids_for_external_ids(
            self, external_ids: List[str]) -> Dict[str, List[str]]:
        """
        Returns a list of data row ids for a list of external ids.
        There is a max of 1500 items returned at a time.

        Args:
            external_ids: List of external ids to fetch data row ids for
        Returns:
            A dict of external ids as keys and values as a list of data row ids that correspond to that external id.
        """
        query_str = """query externalIdsToDataRowIdsPyApi($externalId_in: [String!]!){
            externalIdsToDataRowIds(externalId_in: $externalId_in) { dataRowId externalId }
        }
        """
        max_ids_per_request = 100
        result = defaultdict(list)
        for i in range(0, len(external_ids), max_ids_per_request):
            for row in self.execute(
                    query_str,
                {'externalId_in': external_ids[i:i + max_ids_per_request]
                })['externalIdsToDataRowIds']:
                result[row['externalId']].append(row['dataRowId'])
        return result

    def get_ontology(self, ontology_id) -> Ontology:
        """
        Fetches an Ontology by id.

        Args:
            ontology_id (str): The id of the ontology to query for
        Returns:
            Ontology
        """
        return self._get_single(Entity.Ontology, ontology_id)

    def get_ontologies(self, name_contains) -> PaginatedCollection:
        """
        Fetches all ontologies with names that match the name_contains string.

        Args:
            name_contains (str): the string to search ontology names by
        Returns:
            PaginatedCollection of Ontologies with names that match `name_contains`
        """
        query_str = """query getOntologiesPyApi($search: String, $filter: OntologyFilter, $from : String, $first: PageSize){
            ontologies(where: {filter: $filter, search: $search}, after: $from, first: $first){
                nodes {%s}
                nextCursor
            }
        }
        """ % query.results_query_part(Entity.Ontology)
        params = {'search': name_contains, 'filter': {'status': 'ALL'}}
        return PaginatedCollection(self, query_str, params,
                                   ['ontologies', 'nodes'], Entity.Ontology,
                                   ['ontologies', 'nextCursor'])

    def get_feature_schema(self, feature_schema_id):
        """
        Fetches a feature schema. Only supports top level feature schemas.

        Args:
            feature_schema_id (str): The id of the feature schema to query for
        Returns:
            FeatureSchema
        """

        query_str = """query rootSchemaNodePyApi($rootSchemaNodeWhere: RootSchemaNodeWhere!){
              rootSchemaNode(where: $rootSchemaNodeWhere){%s}
        }""" % query.results_query_part(Entity.FeatureSchema)
        res = self.execute(
            query_str,
            {'rootSchemaNodeWhere': {
                'featureSchemaId': feature_schema_id
            }})['rootSchemaNode']
        res['id'] = res['normalized']['featureSchemaId']
        return Entity.FeatureSchema(self, res)

    def get_feature_schemas(self, name_contains) -> PaginatedCollection:
        """
        Fetches top level feature schemas with names that match the `name_contains` string

        Args:
            name_contains (str): the string to search top level feature schema names by
        Returns:
            PaginatedCollection of FeatureSchemas with names that match `name_contains`
        """
        query_str = """query rootSchemaNodesPyApi($search: String, $filter: RootSchemaNodeFilter, $from : String, $first: PageSize){
            rootSchemaNodes(where: {filter: $filter, search: $search}, after: $from, first: $first){
                nodes {%s}
                nextCursor
            }
        }
        """ % query.results_query_part(Entity.FeatureSchema)
        params = {'search': name_contains, 'filter': {'status': 'ALL'}}

        def rootSchemaPayloadToFeatureSchema(client, payload):
            # Technically we are querying for a Schema Node.
            # But the features are the same so we just grab the feature schema id
            payload['id'] = payload['normalized']['featureSchemaId']
            return Entity.FeatureSchema(client, payload)

        return PaginatedCollection(self, query_str, params,
                                   ['rootSchemaNodes', 'nodes'],
                                   rootSchemaPayloadToFeatureSchema,
                                   ['rootSchemaNodes', 'nextCursor'])

    def create_ontology_from_feature_schemas(self,
                                             name,
                                             feature_schema_ids,
                                             media_type=None) -> Ontology:
        """
        Creates an ontology from a list of feature schema ids

        Args:
            name (str): Name of the ontology
            feature_schema_ids (List[str]): List of feature schema ids corresponding to
                top level tools and classifications to include in the ontology
            media_type (MediaType or None): Media type of a new ontology
        Returns:
            The created Ontology
        """
        tools, classifications = [], []
        for feature_schema_id in feature_schema_ids:
            feature_schema = self.get_feature_schema(feature_schema_id)
            tool = ['tool']
            if 'tool' in feature_schema.normalized:
                tool = feature_schema.normalized['tool']
                try:
                    Tool.Type(tool)
                    tools.append(feature_schema.normalized)
                except ValueError:
                    raise ValueError(
                        f"Tool `{tool}` not in list of supported tools.")
            elif 'type' in feature_schema.normalized:
                classification = feature_schema.normalized['type']
                try:
                    Classification.Type(classification)
                    classifications.append(feature_schema.normalized)
                except ValueError:
                    raise ValueError(
                        f"Classification `{classification}` not in list of supported classifications."
                    )
            else:
                raise ValueError(
                    "Neither `tool` or `classification` found in the normalized feature schema"
                )
        normalized = {'tools': tools, 'classifications': classifications}
        return self.create_ontology(name, normalized, media_type)

    def create_ontology(self, name, normalized, media_type=None) -> Ontology:
        """
        Creates an ontology from normalized data
            >>> normalized = {"tools" : [{'tool': 'polygon',  'name': 'cat', 'color': 'black'}], "classifications" : []}
            >>> ontology = client.create_ontology("ontology-name", normalized)

        Or use the ontology builder. It is especially useful for complex ontologies
            >>> normalized = OntologyBuilder(tools=[Tool(tool=Tool.Type.BBOX, name="cat", color = 'black')]).asdict()
            >>> ontology = client.create_ontology("ontology-name", normalized)

        To reuse existing feature schemas, use `create_ontology_from_feature_schemas()`
        More details can be found here:
            https://github.com/Labelbox/labelbox-python/blob/develop/examples/basics/ontologies.ipynb

        Args:
            name (str): Name of the ontology
            normalized (dict): A normalized ontology payload. See above for details.
            media_type (MediaType or None): Media type of a new ontology
        Returns:
            The created Ontology
        """

        if media_type:
            if MediaType.is_supported(media_type):
                media_type = media_type.value
            else:
                raise get_media_type_validation_error(media_type)

        query_str = """mutation upsertRootSchemaNodePyApi($data:  UpsertOntologyInput!){
                           upsertOntology(data: $data){ %s }
        } """ % query.results_query_part(Entity.Ontology)
        params = {
            'data': {
                'name': name,
                'normalized': json.dumps(normalized),
                'mediaType': media_type
            }
        }
        res = self.execute(query_str, params)
        return Entity.Ontology(self, res['upsertOntology'])

    def create_feature_schema(self, normalized):
        """
        Creates a feature schema from normalized data.
            >>> normalized = {'tool': 'polygon',  'name': 'cat', 'color': 'black'}
            >>> feature_schema = client.create_feature_schema(normalized)

        Or use the Tool or Classification objects. It is especially useful for complex tools.
            >>> normalized = Tool(tool=Tool.Type.BBOX, name="cat", color = 'black').asdict()
            >>> feature_schema = client.create_feature_schema(normalized)

        Subclasses are also supported
            >>> normalized =  Tool(
                    tool=Tool.Type.SEGMENTATION,
                    name="cat",
                    classifications=[
                        Classification(
                            class_type=Classification.Type.TEXT,
                            instructions="name"
                        )
                    ]
                )
            >>> feature_schema = client.create_feature_schema(normalized)

        More details can be found here:
            https://github.com/Labelbox/labelbox-python/blob/develop/examples/basics/ontologies.ipynb

        Args:
            normalized (dict): A normalized tool or classification payload. See above for details
        Returns:
            The created FeatureSchema.
        """
        query_str = """mutation upsertRootSchemaNodePyApi($data:  UpsertRootSchemaNodeInput!){
                        upsertRootSchemaNode(data: $data){ %s }
        } """ % query.results_query_part(Entity.FeatureSchema)
        normalized = {k: v for k, v in normalized.items() if v}
        params = {'data': {'normalized': json.dumps(normalized)}}
        res = self.execute(query_str, params)['upsertRootSchemaNode']
        # Technically we are querying for a Schema Node.
        # But the features are the same so we just grab the feature schema id
        res['id'] = res['normalized']['featureSchemaId']
        return Entity.FeatureSchema(self, res)

    def get_model_run(self, model_run_id: str) -> ModelRun:
        """ Gets a single ModelRun with the given ID.

            >>> model_run = client.get_model_run("<model_run_id>")

        Args:
            model_run_id (str): Unique ID of the ModelRun.
        Returns:
            A ModelRun object.
        """
        return self._get_single(Entity.ModelRun, model_run_id)

    def assign_global_keys_to_data_rows(
            self,
            global_key_to_data_row_inputs: List[Dict[str, str]],
            timeout_seconds=60) -> Dict[str, Union[str, List[Any]]]:
        """
        Assigns global keys to data rows.

        Args:
            A list of dicts containing data_row_id and global_key.
        Returns:
            Dictionary containing 'status', 'results' and 'errors'.

            'Status' contains the outcome of this job. It can be one of
            'Success', 'Partial Success', or 'Failure'.

            'Results' contains the successful global_key assignments, including
            global_keys that have been sanitized to Labelbox standards.

            'Errors' contains global_key assignments that failed, along with
            the reasons for failure.
        Examples:
            >>> global_key_data_row_inputs = [
                {"data_row_id": "cl7asgri20yvo075b4vtfedjb", "global_key": "key1"},
                {"data_row_id": "cl7asgri10yvg075b4pz176ht", "global_key": "key2"},
                ]
            >>> job_result = client.assign_global_keys_to_data_rows(global_key_data_row_inputs)
            >>> print(job_result['status'])
            Partial Success
            >>> print(job_result['results'])
            [{'data_row_id': 'cl7tv9wry00hlka6gai588ozv', 'global_key': 'gk', 'sanitized': False}]
            >>> print(job_result['errors'])
            [{'data_row_id': 'cl7tpjzw30031ka6g4evqdfoy', 'global_key': 'gk"', 'error': 'Invalid global key'}]
        """

        def _format_successful_rows(rows: Dict[str, str],
                                    sanitized: bool) -> List[Dict[str, str]]:
            return [{
                'data_row_id': r['dataRowId'],
                'global_key': r['globalKey'],
                'sanitized': sanitized
            } for r in rows]

        def _format_failed_rows(rows: Dict[str, str],
                                error_msg: str) -> List[Dict[str, str]]:
            return [{
                'data_row_id': r['dataRowId'],
                'global_key': r['globalKey'],
                'error': error_msg
            } for r in rows]

        # Validate input dict
        validation_errors = []
        for input in global_key_to_data_row_inputs:
            if "data_row_id" not in input or "global_key" not in input:
                validation_errors.append(input)
        if len(validation_errors) > 0:
            raise ValueError(
                f"Must provide a list of dicts containing both `data_row_id` and `global_key`. The following dict(s) are invalid: {validation_errors}."
            )

        # Start assign global keys to data rows job
        query_str = """mutation assignGlobalKeysToDataRowsPyApi($globalKeyDataRowLinks: [AssignGlobalKeyToDataRowInput!]!) {
            assignGlobalKeysToDataRows(data: {assignInputs: $globalKeyDataRowLinks}) {
                jobId
            }
        }
        """
        params = {
            'globalKeyDataRowLinks': [{
                utils.camel_case(key): value for key, value in input.items()
            } for input in global_key_to_data_row_inputs]
        }
        assign_global_keys_to_data_rows_job = self.execute(query_str, params)

        # Query string for retrieving job status and result, if job is done
        result_query_str = """query assignGlobalKeysToDataRowsResultPyApi($jobId: ID!) {
            assignGlobalKeysToDataRowsResult(jobId: {id: $jobId}) {
                jobStatus
                data {
                    sanitizedAssignments {
                        dataRowId
                        globalKey
                    }
                    invalidGlobalKeyAssignments {
                        dataRowId
                        globalKey
                    }
                    unmodifiedAssignments {
                        dataRowId
                        globalKey
                    }
                    accessDeniedAssignments {
                        dataRowId
                        globalKey
                    }
                }}}
        """
        result_params = {
            "jobId":
                assign_global_keys_to_data_rows_job["assignGlobalKeysToDataRows"
                                                   ]["jobId"]
        }

        # Poll job status until finished, then retrieve results
        sleep_time = 2
        start_time = time.time()
        while True:
            res = self.execute(result_query_str, result_params)
            if res["assignGlobalKeysToDataRowsResult"][
                    "jobStatus"] == "COMPLETE":
                results, errors = [], []
                res = res['assignGlobalKeysToDataRowsResult']['data']
                # Successful assignments
                results.extend(
                    _format_successful_rows(rows=res['sanitizedAssignments'],
                                            sanitized=True))
                results.extend(
                    _format_successful_rows(rows=res['unmodifiedAssignments'],
                                            sanitized=False))
                # Failed assignments
                errors.extend(
                    _format_failed_rows(rows=res['invalidGlobalKeyAssignments'],
                                        error_msg="Invalid global key"))
                errors.extend(
                    _format_failed_rows(rows=res['accessDeniedAssignments'],
                                        error_msg="Access denied to Data Row"))

                if not errors:
                    status = CollectionJobStatus.SUCCESS.value
                elif errors and results:
                    status = CollectionJobStatus.PARTIAL_SUCCESS.value
                else:
                    status = CollectionJobStatus.FAILURE.value

                if errors:
                    logger.warning(
                        "There are errors present. Please look at 'errors' in the returned dict for more details"
                    )

                return {
                    "status": status,
                    "results": results,
                    "errors": errors,
                }
            elif res["assignGlobalKeysToDataRowsResult"][
                    "jobStatus"] == "FAILED":
                raise labelbox.exceptions.LabelboxError(
                    "Job assign_global_keys_to_data_rows failed.")
            current_time = time.time()
            if current_time - start_time > timeout_seconds:
                raise labelbox.exceptions.TimeoutError(
                    "Timed out waiting for assign_global_keys_to_data_rows job to complete."
                )
            time.sleep(sleep_time)

    def get_data_row_ids_for_global_keys(
            self,
            global_keys: List[str],
            timeout_seconds=60) -> Dict[str, Union[str, List[Any]]]:
        """
        Gets data row ids for a list of global keys.

        Args:
            A list of global keys
        Returns:
            Dictionary containing 'status', 'results' and 'errors'.

            'Status' contains the outcome of this job. It can be one of
            'Success', 'Partial Success', or 'Failure'.

            'Results' contains a list of the fetched corresponding data row ids in the input order. 
            For data rows that cannot be fetched due to an error, or data rows that do not exist, 
            empty string is returned at the position of the respective global_key. 
            More error information can be found in the 'Errors' section.

            'Errors' contains a list of global_keys that could not be fetched, along
            with the failure reason
        Examples:
            >>> job_result = client.get_data_row_ids_for_global_keys(["key1","key2"])
            >>> print(job_result['status'])
            Partial Success
            >>> print(job_result['results'])
            ['cl7tv9wry00hlka6gai588ozv', 'cl7tv9wxg00hpka6gf8sh81bj']
            >>> print(job_result['errors'])
            [{'global_key': 'asdf', 'error': 'Data Row not found'}]
        """

        def _format_failed_rows(rows: List[str],
                                error_msg: str) -> List[Dict[str, str]]:
            return [{'global_key': r, 'error': error_msg} for r in rows]

        # Start get data rows for global keys job
        query_str = """query getDataRowsForGlobalKeysPyApi($globalKeys: [ID!]!) {
            dataRowsForGlobalKeys(where: {ids: $globalKeys}) { jobId}}
            """
        params = {"globalKeys": global_keys}
        data_rows_for_global_keys_job = self.execute(query_str, params)

        # Query string for retrieving job status and result, if job is done
        result_query_str = """query getDataRowsForGlobalKeysResultPyApi($jobId: ID!) {
            dataRowsForGlobalKeysResult(jobId: {id: $jobId}) { data {
                fetchedDataRows { id }
                notFoundGlobalKeys
                accessDeniedGlobalKeys
                deletedDataRowGlobalKeys
                } jobStatus}}
            """
        result_params = {
            "jobId":
                data_rows_for_global_keys_job["dataRowsForGlobalKeys"]["jobId"]
        }

        # Poll job status until finished, then retrieve results
        sleep_time = 2
        start_time = time.time()
        while True:
            res = self.execute(result_query_str, result_params)
            if res["dataRowsForGlobalKeysResult"]['jobStatus'] == "COMPLETE":
                data = res["dataRowsForGlobalKeysResult"]['data']
                results, errors = [], []
                results.extend([row['id'] for row in data['fetchedDataRows']])
                errors.extend(
                    _format_failed_rows(data['notFoundGlobalKeys'],
                                        "Data Row not found"))
                errors.extend(
                    _format_failed_rows(data['accessDeniedGlobalKeys'],
                                        "Access denied to Data Row"))
                errors.extend(
                    _format_failed_rows(data['deletedDataRowGlobalKeys'],
                                        "Data Row deleted"))

                # Invalid results may contain empty string, so we must filter
                # them prior to checking for PARTIAL_SUCCESS
                filtered_results = list(filter(lambda r: r != '', results))
                if not errors:
                    status = CollectionJobStatus.SUCCESS.value
                elif errors and len(filtered_results) > 0:
                    status = CollectionJobStatus.PARTIAL_SUCCESS.value
                else:
                    status = CollectionJobStatus.FAILURE.value

                if errors:
                    logger.warning(
                        "There are errors present. Please look at 'errors' in the returned dict for more details"
                    )

                return {"status": status, "results": results, "errors": errors}
            elif res["dataRowsForGlobalKeysResult"]['jobStatus'] == "FAILED":
                raise labelbox.exceptions.LabelboxError(
                    "Job dataRowsForGlobalKeys failed.")
            current_time = time.time()
            if current_time - start_time > timeout_seconds:
                raise labelbox.exceptions.TimeoutError(
                    "Timed out waiting for get_data_rows_for_global_keys job to complete."
                )
            time.sleep(sleep_time)

    def clear_global_keys(
            self,
            global_keys: List[str],
            timeout_seconds=60) -> Dict[str, Union[str, List[Any]]]:
        """
        Clears global keys for the data rows tha correspond to the global keys provided.

        Args:
            A list of global keys
        Returns:
            Dictionary containing 'status', 'results' and 'errors'.

            'Status' contains the outcome of this job. It can be one of
            'Success', 'Partial Success', or 'Failure'.

            'Results' contains a list global keys that were successfully cleared.

            'Errors' contains a list of global_keys correspond to the data rows that could not be
            modified, accessed by the user, or not found.
        Examples:
            >>> job_result = client.get_data_row_ids_for_global_keys(["key1","key2"])
            >>> print(job_result['status'])
            Partial Success
            >>> print(job_result['results'])
            ['cl7tv9wry00hlka6gai588ozv', 'cl7tv9wxg00hpka6gf8sh81bj']
            >>> print(job_result['errors'])
            [{'global_key': 'asdf', 'error': 'Data Row not found'}]
        """

        def _format_failed_rows(rows: List[str],
                                error_msg: str) -> List[Dict[str, str]]:
            return [{'global_key': r, 'error': error_msg} for r in rows]

        # Start get data rows for global keys job
        query_str = """mutation clearGlobalKeysPyApi($globalKeys: [ID!]!) {
            clearGlobalKeys(where: {ids: $globalKeys}) { jobId}}
            """
        params = {"globalKeys": global_keys}
        clear_global_keys_job = self.execute(query_str, params)

        # Query string for retrieving job status and result, if job is done
        result_query_str = """query clearGlobalKeysResultPyApi($jobId: ID!) {
            clearGlobalKeysResult(jobId: {id: $jobId}) { data {
                clearedGlobalKeys
                failedToClearGlobalKeys
                notFoundGlobalKeys
                accessDeniedGlobalKeys
                } jobStatus}}
            """
        result_params = {
            "jobId": clear_global_keys_job["clearGlobalKeys"]["jobId"]
        }
        # Poll job status until finished, then retrieve results
        sleep_time = 2
        start_time = time.time()
        while True:
            res = self.execute(result_query_str, result_params)
            if res["clearGlobalKeysResult"]['jobStatus'] == "COMPLETE":
                data = res["clearGlobalKeysResult"]['data']
                results, errors = [], []
                results.extend(data['clearedGlobalKeys'])
                errors.extend(
                    _format_failed_rows(data['failedToClearGlobalKeys'],
                                        "Clearing global key failed"))
                errors.extend(
                    _format_failed_rows(
                        data['notFoundGlobalKeys'],
                        "Failed to find data row matching provided global key"))
                errors.extend(
                    _format_failed_rows(
                        data['accessDeniedGlobalKeys'],
                        "Denied access to modify data row matching provided global key"
                    ))

                if not errors:
                    status = CollectionJobStatus.SUCCESS.value
                elif errors and len(results) > 0:
                    status = CollectionJobStatus.PARTIAL_SUCCESS.value
                else:
                    status = CollectionJobStatus.FAILURE.value

                if errors:
                    logger.warning(
                        "There are errors present. Please look at 'errors' in the returned dict for more details"
                    )

                return {"status": status, "results": results, "errors": errors}
            elif res["clearGlobalKeysResult"]['jobStatus'] == "FAILED":
                raise labelbox.exceptions.LabelboxError(
                    "Job clearGlobalKeys failed.")
            current_time = time.time()
            if current_time - start_time > timeout_seconds:
                raise labelbox.exceptions.TimeoutError(
                    "Timed out waiting for clear_global_keys job to complete.")
            time.sleep(sleep_time)

    def get_catalog_slice(self, slice_id) -> CatalogSlice:
        """
        Fetches a Catalog Slice by ID.

        Args:
             slice_id (str): The ID of the Slice
        Returns:
            CatalogSlice
        """
        query_str = """
            query getSavedQueryPyApi($id: ID!) {
                getSavedQuery(id: $id) {
                    id
                    name
                    description
                    filter
                    createdAt
                    updatedAt
                }
            }
        """
        res = self.execute(query_str, {'id': slice_id})
        return Entity.CatalogSlice(self, res['getSavedQuery'])
