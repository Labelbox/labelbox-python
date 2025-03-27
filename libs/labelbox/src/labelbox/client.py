# type: ignore
import json
import logging
import mimetypes
import os
import random
import time
import urllib.parse
import warnings
from collections import defaultdict
from types import MappingProxyType
from typing import Any, Callable, Dict, List, Optional, Set, Union

import requests
import requests.exceptions
from google.api_core import retry
from lbox.exceptions import (
    InternalServerError,
    LabelboxError,
    ResourceNotFoundError,
    TimeoutError,
)
from lbox.request_client import RequestClient

from labelbox import __version__ as SDK_VERSION
from labelbox import utils
from labelbox.adv_client import AdvClient
from labelbox.orm import query
from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Entity, Field
from labelbox.pagination import PaginatedCollection
from labelbox.project_validation import _CoreProjectInput
from labelbox.schema import role
from labelbox.schema.catalog import Catalog
from labelbox.schema.data_row import DataRow
from labelbox.schema.data_row_metadata import DataRowMetadataOntology
from labelbox.schema.dataset import Dataset
from labelbox.schema.embedding import Embedding
from labelbox.schema.enums import CollectionJobStatus
from labelbox.schema.foundry.foundry_client import FoundryClient
from labelbox.schema.iam_integration import IAMIntegration
from labelbox.schema.identifiables import DataRowIds, GlobalKeys
from labelbox.schema.label_score import LabelScore
from labelbox.schema.labeling_frontend import LabelingFrontend
from labelbox.schema.labeling_service_dashboard import LabelingServiceDashboard
from labelbox.schema.media_type import (
    MediaType,
    get_media_type_validation_error,
)
from labelbox.schema.model import Model
from labelbox.schema.model_config import ModelConfig
from labelbox.schema.model_run import ModelRun
from labelbox.schema.ontology import (
    Classification,
    DeleteFeatureFromOntologyResult,
    FeatureSchema,
    Ontology,
    PromptResponseClassification,
    tool_type_cls_from_type,
)
from labelbox.schema.ontology_kind import (
    EditorTaskType,
    EditorTaskTypeMapper,
    OntologyKind,
)
from labelbox.schema.organization import Organization
from labelbox.schema.project import Project
from labelbox.schema.quality_mode import (
    QualityMode,
)
from labelbox.schema.role import Role
from labelbox.schema.search_filters import SearchFilter
from labelbox.schema.send_to_annotate_params import (
    SendToAnnotateFromCatalogParams,
    build_annotations_input,
    build_destination_task_queue_input,
    build_predictions_input,
)
from labelbox.schema.slice import CatalogSlice, ModelSlice
from labelbox.schema.task import DataUpsertTask, Task
from labelbox.schema.user import User
from labelbox.schema.taskstatus import TaskStatus
from labelbox.schema.api_key import ApiKey
from labelbox.schema.timeunit import TimeUnit

logger = logging.getLogger(__name__)


class Client:
    """A Labelbox client.

    Provides functions for querying and creating
    top-level data objects (Projects, Datasets).
    """

    # Class variable to cache task types
    _cancelable_task_types = None

    def __init__(
        self,
        api_key=None,
        endpoint="https://api.labelbox.com/graphql",
        enable_experimental=False,
        app_url="https://app.labelbox.com",
        rest_endpoint="https://api.labelbox.com/api/v1",
    ):
        """Creates and initializes a Labelbox Client.

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
            AuthenticationError: If no `api_key`
                is provided as an argument or via the environment
                variable.
        """
        self._data_row_metadata_ontology = None
        self._request_client = RequestClient(
            sdk_version=SDK_VERSION,
            api_key=api_key,
            endpoint=endpoint,
            enable_experimental=enable_experimental,
            app_url=app_url,
            rest_endpoint=rest_endpoint,
        )
        self._adv_client = AdvClient.factory(rest_endpoint, api_key)

    @property
    def headers(self) -> MappingProxyType:
        return self._request_client.headers

    @property
    def connection(self) -> requests.Session:
        return self._request_client._connection

    @property
    def endpoint(self) -> str:
        return self._request_client.endpoint

    @property
    def rest_endpoint(self) -> str:
        return self._request_client.rest_endpoint

    @property
    def enable_experimental(self) -> bool:
        return self._request_client.enable_experimental

    @enable_experimental.setter
    def enable_experimental(self, value: bool):
        self._request_client.enable_experimental = value

    @property
    def app_url(self) -> str:
        return self._request_client.app_url

    def set_sdk_method(self, sdk_method: str):
        self._request_client.sdk_method = sdk_method

    def unset_sdk_method(self):
        self._request_client.sdk_method = None

    def execute(
        self,
        query=None,
        params=None,
        data=None,
        files=None,
        timeout=60.0,
        experimental=False,
        error_log_key="message",
        raise_return_resource_not_found=False,
        error_handlers: Optional[
            Dict[str, Callable[[requests.models.Response], None]]
        ] = None,
    ) -> Dict[str, Any]:
        """Executes a GraphQL query.

        Args:
            query (str): The query to execute.
            params (dict): Variables to pass to the query.
            data (dict): Includes the query and variables as well as the map for file upload multipart/form-data requests as per GraphQL multipart request specification.
            files (dict): File descriptors to pass to the query for file upload multipart/form-data requests.
            timeout (float): Timeout for the request.
            experimental (bool): Whether to use experimental features.
            error_log_key (str): Key to use for error logging.
            raise_return_resource_not_found (bool): If True, raise a
                ResourceNotFoundError if the query returns None.
            error_handlers (dict): A dictionary mapping graphql error code to handler functions.
                Allows a caller to handle specific errors reporting in a custom way or produce more user-friendly readable messages

        Returns:
            dict: The response from the server.

        See UserGroupV2.upload_members for an example of how to use this method for file upload.
        """
        return self._request_client.execute(
            query,
            params,
            data=data,
            files=files,
            timeout=timeout,
            experimental=experimental,
            error_log_key=error_log_key,
            raise_return_resource_not_found=raise_return_resource_not_found,
            error_handlers=error_handlers,
        )

    def upload_file(self, path: str) -> str:
        """Uploads given path to local file.

        Also includes best guess at the content type of the file.

        Args:
            path (str): path to local file to be uploaded.
        Returns:
            str, the URL of uploaded data.
        Raises:
            LabelboxError: If upload failed.
        """
        content_type, _ = mimetypes.guess_type(path)
        filename = os.path.basename(path)
        with open(path, "rb") as f:
            return self.upload_data(
                content=f.read(), filename=filename, content_type=content_type
            )

    @retry.Retry(predicate=retry.if_exception_type(InternalServerError))
    def upload_data(
        self,
        content: bytes,
        filename: str = None,
        content_type: str = None,
        sign: bool = False,
    ) -> str:
        """Uploads the given data (bytes) to Labelbox.

        Args:
            content: bytestring to upload
            filename: name of the upload
            content_type: content type of data uploaded
            sign: whether or not to sign the url

        Returns:
            str, the URL of uploaded data.

        Raises:
            LabelboxError: If upload failed.
        """

        request_data = {
            "operations": json.dumps(
                {
                    "variables": {
                        "file": None,
                        "contentLength": len(content),
                        "sign": sign,
                    },
                    "query": """mutation UploadFile($file: Upload!, $contentLength: Int!,
                                            $sign: Boolean) {
                            uploadFile(file: $file, contentLength: $contentLength,
                                       sign: $sign) {url filename} } """,
                }
            ),
            "map": (None, json.dumps({"1": ["variables.file"]})),
        }

        files = {
            "1": (filename, content, content_type)
            if (filename and content_type)
            else content
        }
        file_data = self.execute(data=request_data, files=files)

        return file_data["uploadFile"]["url"]

    def _get_single(self, db_object_type, uid):
        """Fetches a single object of the given type, for the given ID.

        Args:
            db_object_type (type): DbObject subclass.
            uid (str): Unique ID of the row.
        Returns:
            Object of `db_object_type`.
        Raises:
            ResourceNotFoundError: If there is no object
                of the given type for the given ID.
        """
        query_str, params = query.get_single(db_object_type, uid)

        res = self.execute(query_str, params)
        res = res and res.get(utils.camel_case(db_object_type.type_name()))
        if res is None:
            raise ResourceNotFoundError(db_object_type, params)
        else:
            return db_object_type(self, res)

    def get_project(self, project_id) -> Project:
        """Gets a single Project with the given ID.

        >>> project = client.get_project("<project_id>")

        Args:
            project_id (str): Unique ID of the Project.
        Returns:
            The sought Project.
        Raises:
            ResourceNotFoundError: If there is no
                Project with the given ID.
        """
        return self._get_single(Entity.Project, project_id)

    def get_dataset(self, dataset_id) -> Dataset:
        """Gets a single Dataset with the given ID.

        >>> dataset = client.get_dataset("<dataset_id>")

        Args:
            dataset_id (str): Unique ID of the Dataset.
        Returns:
            The sought Dataset.
        Raises:
            ResourceNotFoundError: If there is no
                Dataset with the given ID.
        """
        return self._get_single(Entity.Dataset, dataset_id)

    def get_user(self) -> User:
        """Gets the current User database object.

        >>> user = client.get_user()
        """
        return self._get_single(Entity.User, None)

    def get_organization(self) -> Organization:
        """Gets the Organization DB object of the current user.

        >>> organization = client.get_organization()
        """
        return self._get_single(Entity.Organization, None)

    def _get_all(self, db_object_type, where, filter_deleted=True):
        """Fetches all the objects of the given type the user has access to.

        Args:
            db_object_type (type): DbObject subclass.
            where (Comparison, LogicalOperation or None): The `where` clause
                for filtering.
        Returns:
            An iterable of `db_object_type` instances.
        """
        if filter_deleted:
            not_deleted = db_object_type.deleted == False  # noqa: E712 <Gabefire> Needed for bit operator to combine comparisons
            where = not_deleted if where is None else where & not_deleted
        query_str, params = query.get_all(db_object_type, where)

        return PaginatedCollection(
            self,
            query_str,
            params,
            [utils.camel_case(db_object_type.type_name()) + "s"],
            db_object_type,
        )

    def get_projects(self, where=None) -> PaginatedCollection:
        """Fetches all the projects the user has access to.

        >>> projects = client.get_projects(where=(Project.name == "<project_name>") & (Project.description == "<project_description>"))

        Args:
            where (Comparison, LogicalOperation or None): The `where` clause
                for filtering.
        Returns:
            PaginatedCollection of all projects the user has access to or projects matching the criteria specified.
        """
        return self._get_all(Entity.Project, where)

    def get_users(self, where=None) -> PaginatedCollection:
        """Fetches all the users.

        >>> users = client.get_users(where=User.email == "<user_email>")

        Args:
            where (Comparison, LogicalOperation or None): The `where` clause
                for filtering.
        Returns:
            An iterable of Users (typically a PaginatedCollection).
        """
        return self._get_all(Entity.User, where, filter_deleted=False)

    def get_datasets(self, where=None) -> PaginatedCollection:
        """Fetches one or more datasets.

        >>> datasets = client.get_datasets(where=(Dataset.name == "<dataset_name>") & (Dataset.description == "<dataset_description>"))

        Args:
            where (Comparison, LogicalOperation or None): The `where` clause
                for filtering.
        Returns:
            PaginatedCollection of all datasets the user has access to or datasets matching the criteria specified.
        """
        return self._get_all(Entity.Dataset, where)

    def _get_labeling_frontends(self, where=None) -> List[LabelingFrontend]:
        """Private method to obtain labeling front ends"""
        return self._get_all(Entity.LabelingFrontend, where)

    def _create(self, db_object_type, data, extra_params={}):
        """Creates an object on the server. Attribute values are
            passed as keyword arguments:

        Args:
            db_object_type (type): A DbObjectType subtype.
            data (dict): Keys are attributes or their names (in Python,
                snake-case convention) and values are desired attribute values.
            extra_params (dict): Additional parameters to pass to GraphQL.
                These have to be Field(...): value pairs.
        Returns:
            A new object of the given DB object type.
        Raises:
            InvalidAttributeError: If the DB object type does not contain
                any of the attribute names given in `data`.
        """
        # Convert string attribute names to Field or Relationship objects.
        # Also convert Labelbox object values to their UIDs.
        data = {
            db_object_type.attribute(attr)
            if isinstance(attr, str)
            else attr: value.uid if isinstance(value, DbObject) else value
            for attr, value in data.items()
        }

        data = {**data, **extra_params}
        query_string, params = query.create(db_object_type, data)
        res = self.execute(
            query_string, params, raise_return_resource_not_found=True
        )
        if not res:
            raise LabelboxError(
                "Failed to create %s" % db_object_type.type_name()
            )
        res = res["create%s" % db_object_type.type_name()]
        return db_object_type(self, res)

    def create_model_config(
        self, name: str, model_id: str, inference_params: dict
    ) -> ModelConfig:
        """Creates a new model config with the given params.
            Model configs are scoped to organizations, and can be reused between projects.

        Args:
            name (str): Name of the model config
            model_id (str): ID of model to configure
            inference_params (dict): JSON of model configuration parameters.

        Returns:
            str, id of the created model config
        """
        if not name:
            raise ValueError("Model config name must not be an empty string.")

        query = """mutation CreateModelConfigPyApi($modelId: ID!, $inferenceParams: Json!, $name: String!)  {
                    createModelConfig(input: {modelId: $modelId, inferenceParams: $inferenceParams, name: $name}) {
                        modelId
                        inferenceParams
                        id
                        name
                    }
                }"""
        params = {
            "modelId": model_id,
            "inferenceParams": inference_params,
            "name": name,
        }
        result = self.execute(query, params)
        return ModelConfig(self, result["createModelConfig"])

    def delete_model_config(self, id: str) -> bool:
        """Deletes an existing model config with the given id

        Args:
            id (str): ID of existing model config

        Returns:
            bool, indicates if the operation was a success.
        """

        query = """mutation DeleteModelConfigPyApi($id: ID!)  {
                    deleteModelConfig(input: {id: $id}) {
                        success
                    }
                }"""
        params = {"id": id}
        result = self.execute(query, params)
        if not result:
            raise ResourceNotFoundError(Entity.ModelConfig, params)
        return result["deleteModelConfig"]["success"]

    def create_dataset(
        self, iam_integration=IAMIntegration._DEFAULT, **kwargs
    ) -> Dataset:
        """Creates a Dataset object on the server.

        Attribute values are passed as keyword arguments.

        Args:
            iam_integration (IAMIntegration) : Uses the default integration.
                Optionally specify another integration or set as None to not use delegated access
            **kwargs: Keyword arguments with Dataset attribute values.
        Returns:
            A new Dataset object.
        Raises:
            InvalidAttributeError: If the Dataset type does not contain
                any of the attribute names given in kwargs.
        Examples:
            Create a dataset
            >>> dataset = client.create_dataset(name="<dataset_name>")
            Create a dataset with description
            >>> dataset = client.create_dataset(name="<dataset_name>", description="<dataset_description>")
        """
        dataset = self._create(Entity.Dataset, kwargs)
        if iam_integration == IAMIntegration._DEFAULT:
            iam_integration = (
                self.get_organization().get_default_iam_integration()
            )

        if iam_integration is None:
            return dataset

        try:
            if not isinstance(iam_integration, IAMIntegration):
                raise TypeError(
                    f"iam integration must be a reference an `IAMIntegration` object. Found {type(iam_integration)}"
                )

            if not iam_integration.valid:
                raise ValueError(
                    "Integration is not valid. Please select another."
                )

            self.execute(
                """mutation setSignerForDatasetPyApi($signerId: ID!, $datasetId: ID!) {
                    setSignerForDataset(data: { signerId: $signerId}, where: {id: $datasetId}){id}}
                """,
                {"signerId": iam_integration.uid, "datasetId": dataset.uid},
            )
            validation_result = self.execute(
                """mutation validateDatasetPyApi($id: ID!){validateDataset(where: {id : $id}){
                    valid checks{name, success}}}
                """,
                {"id": dataset.uid},
            )

            if not validation_result["validateDataset"]["valid"]:
                raise LabelboxError(
                    "IAMIntegration was not successfully added to the dataset."
                )
        except Exception as e:
            dataset.delete()
            raise e
        return dataset

    def create_project(
        self,
        name: str,
        media_type: MediaType,
        description: Optional[str] = None,
        quality_modes: Optional[Set[QualityMode]] = {
            QualityMode.Benchmark,
            QualityMode.Consensus,
        },
        is_benchmark_enabled: Optional[bool] = None,
        is_consensus_enabled: Optional[bool] = None,
    ) -> Project:
        """Creates a Project object on the server.

        Attribute values are passed as keyword arguments.

        >>> project = client.create_project(
                name="<project_name>",
                description="<project_description>",
                media_type=MediaType.Image,
            )

        Args:
            name (str): A name for the project
            description (str): A short summary for the project
            media_type (MediaType): The type of assets that this project will accept
            quality_modes (Optional[List[QualityMode]]): The quality modes to use (e.g. Benchmark, Consensus). Defaults to
                Benchmark.
            is_benchmark_enabled (Optional[bool]): Whether the project supports benchmark. Defaults to None.
            is_consensus_enabled (Optional[bool]): Whether the project supports consensus. Defaults to None.
        Returns:
            A new Project object.
        Raises:
            ValueError: If inputs are invalid.
        """
        input = {
            "name": name,
            "description": description,
            "media_type": media_type,
            "quality_modes": quality_modes,
            "is_benchmark_enabled": is_benchmark_enabled,
            "is_consensus_enabled": is_consensus_enabled,
        }
        return self._create_project(_CoreProjectInput(**input))

    def create_model_evaluation_project(
        self,
        name: str,
        description: Optional[str] = None,
        quality_modes: Optional[Set[QualityMode]] = {
            QualityMode.Benchmark,
            QualityMode.Consensus,
        },
        is_benchmark_enabled: Optional[bool] = None,
        is_consensus_enabled: Optional[bool] = None,
        dataset_id: Optional[str] = None,
        dataset_name: Optional[str] = None,
        data_row_count: Optional[int] = None,
    ) -> Project:
        """
        Use this method exclusively to create a chat model evaluation project.
        Args:
            dataset_name: When creating a new dataset, pass the name
            dataset_id: When using an existing dataset, pass the id
            data_row_count: The number of data row assets to use for the project
            See create_project for additional parameters
        Returns:
            Project: The created project

        Examples:
            >>> client.create_model_evaluation_project(name=project_name, media_type=dataset_name="new data set")
            >>>     This creates a new dataset with a default number of rows (100), creates new project and assigns a batch of the newly created datarows to the project.

            >>> client.create_model_evaluation_project(name=project_name, dataset_name="new data set", data_row_count=10)
            >>>     This creates a new dataset with 10 data rows, creates new project and assigns a batch of the newly created datarows to the project.

            >>> client.create_model_evaluation_project(name=project_name, dataset_id="clr00u8j0j0j0")
            >>>     This creates a new project, and adds 100 datarows to the dataset with id "clr00u8j0j0j0" and assigns a batch of the newly created data rows to the project.

            >>> client.create_model_evaluation_project(name=project_name, dataset_id="clr00u8j0j0j0", data_row_count=10)
            >>>     This creates a new project, and adds 100 datarows to the dataset with id "clr00u8j0j0j0" and assigns a batch of the newly created 10 data rows to the project.

            >>> client.create_model_evaluation_project(name=project_name)
            >>>     This creates a new project with no data rows.

        """
        dataset_name_or_id = dataset_id or dataset_name
        append_to_existing_dataset = bool(dataset_id)

        if dataset_name_or_id:
            if data_row_count is None:
                data_row_count = 100
            warnings.warn(
                "Automatic generation of data rows of live model evaluation projects is deprecated. dataset_name_or_id, append_to_existing_dataset, data_row_count will be removed in a future version.",
                DeprecationWarning,
            )

        media_type = MediaType.Conversational
        editor_task_type = EditorTaskType.ModelChatEvaluation

        input = {
            "name": name,
            "description": description,
            "media_type": media_type,
            "quality_modes": quality_modes,
            "is_benchmark_enabled": is_benchmark_enabled,
            "is_consensus_enabled": is_consensus_enabled,
            "dataset_name_or_id": dataset_name_or_id,
            "append_to_existing_dataset": append_to_existing_dataset,
            "data_row_count": data_row_count,
            "editor_task_type": editor_task_type,
        }
        return self._create_project(_CoreProjectInput(**input))

    def create_offline_model_evaluation_project(
        self,
        name: str,
        description: Optional[str] = None,
        quality_modes: Optional[Set[QualityMode]] = {
            QualityMode.Benchmark,
            QualityMode.Consensus,
        },
        is_benchmark_enabled: Optional[bool] = None,
        is_consensus_enabled: Optional[bool] = None,
    ) -> Project:
        """
        Creates a project for offline model evaluation.
        Args:
            See create_project for parameters
        Returns:
            Project: The created project
        """
        input = {
            "name": name,
            "description": description,
            "media_type": MediaType.Conversational,
            "quality_modes": quality_modes,
            "is_benchmark_enabled": is_benchmark_enabled,
            "is_consensus_enabled": is_consensus_enabled,
            "editor_task_type": EditorTaskType.OfflineModelChatEvaluation,
        }
        return self._create_project(_CoreProjectInput(**input))

    def create_prompt_response_generation_project(
        self,
        name: str,
        media_type: MediaType,
        description: Optional[str] = None,
        auto_audit_percentage: Optional[float] = None,
        auto_audit_number_of_labels: Optional[int] = None,
        quality_modes: Optional[Set[QualityMode]] = {
            QualityMode.Benchmark,
            QualityMode.Consensus,
        },
        is_benchmark_enabled: Optional[bool] = None,
        is_consensus_enabled: Optional[bool] = None,
        dataset_id: Optional[str] = None,
        dataset_name: Optional[str] = None,
        data_row_count: int = 100,
    ) -> Project:
        """
        Use this method exclusively to create a prompt and response generation project.

        Args:
            dataset_name: When creating a new dataset, pass the name
            dataset_id: When using an existing dataset, pass the id
            data_row_count: The number of data row assets to use for the project
            media_type: The type of assets that this project will accept. Limited to LLMPromptCreation and LLMPromptResponseCreation
            See create_project for additional parameters
        Returns:
            Project: The created project

        NOTE: Only a dataset_name or dataset_id should be included

        Examples:
            >>> client.create_prompt_response_generation_project(name=project_name, dataset_name="new data set", media_type=MediaType.LLMPromptResponseCreation)
            >>>     This creates a new dataset with a default number of rows (100), creates new prompt and response creation project and assigns a batch of the newly created data rows to the project.

            >>> client.create_prompt_response_generation_project(name=project_name, dataset_name="new data set", data_row_count=10, media_type=MediaType.LLMPromptCreation)
            >>>     This creates a new dataset with 10 data rows, creates new prompt creation project and assigns a batch of the newly created datarows to the project.

            >>> client.create_prompt_response_generation_project(name=project_name, dataset_id="clr00u8j0j0j0", media_type=MediaType.LLMPromptCreation)
            >>>     This creates a new prompt creation project, and adds 100 datarows to the dataset with id "clr00u8j0j0j0" and assigns a batch of the newly created data rows to the project.

            >>> client.create_prompt_response_generation_project(name=project_name, dataset_id="clr00u8j0j0j0", data_row_count=10, media_type=MediaType.LLMPromptResponseCreation)
            >>>     This creates a new prompt and response creation project, and adds 100 datarows to the dataset with id "clr00u8j0j0j0" and assigns a batch of the newly created 10 data rows to the project.

        """
        if not dataset_id and not dataset_name:
            raise ValueError(
                "dataset_name or dataset_id must be present and not be an empty string."
            )

        if dataset_id and dataset_name:
            raise ValueError(
                "Only provide a dataset_name or dataset_id, not both."
            )

        if dataset_id:
            append_to_existing_dataset = True
            dataset_name_or_id = dataset_id
        else:
            append_to_existing_dataset = False
            dataset_name_or_id = dataset_name

        if media_type not in [
            MediaType.LLMPromptCreation,
            MediaType.LLMPromptResponseCreation,
        ]:
            raise ValueError(
                "media_type must be either LLMPromptCreation or LLMPromptResponseCreation"
            )

        input = {
            "name": name,
            "description": description,
            "media_type": media_type,
            "auto_audit_percentage": auto_audit_percentage,
            "auto_audit_number_of_labels": auto_audit_number_of_labels,
            "quality_modes": quality_modes,
            "is_benchmark_enabled": is_benchmark_enabled,
            "is_consensus_enabled": is_consensus_enabled,
            "dataset_name_or_id": dataset_name_or_id,
            "append_to_existing_dataset": append_to_existing_dataset,
            "data_row_count": data_row_count,
        }
        return self._create_project(_CoreProjectInput(**input))

    def create_response_creation_project(
        self,
        name: str,
        description: Optional[str] = None,
        quality_modes: Optional[Set[QualityMode]] = {
            QualityMode.Benchmark,
            QualityMode.Consensus,
        },
        is_benchmark_enabled: Optional[bool] = None,
        is_consensus_enabled: Optional[bool] = None,
    ) -> Project:
        """
        Creates a project for response creation.
        Args:
            See create_project for parameters
        Returns:
            Project: The created project
        """
        input = {
            "name": name,
            "description": description,
            "media_type": MediaType.Text,  # Only Text is supported
            "quality_modes": quality_modes,
            "is_benchmark_enabled": is_benchmark_enabled,
            "is_consensus_enabled": is_consensus_enabled,
            "editor_task_type": EditorTaskType.ResponseCreation.value,  # Special editor task type for response creation projects
        }
        return self._create_project(_CoreProjectInput(**input))

    def _create_project(self, input: _CoreProjectInput) -> Project:
        params = input.model_dump(exclude_none=True)

        extra_params = {
            Field.String("dataset_name_or_id"): params.pop(
                "dataset_name_or_id", None
            ),
            Field.Boolean("append_to_existing_dataset"): params.pop(
                "append_to_existing_dataset", None
            ),
        }
        extra_params = {k: v for k, v in extra_params.items() if v is not None}
        return self._create(Entity.Project, params, extra_params)

    def get_roles(self) -> Dict[str, Role]:
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

    def get_data_row_by_global_key(self, global_key: str) -> DataRow:
        """
        Returns: DataRow: returns a single data row given the global key
        """
        res = self.get_data_row_ids_for_global_keys([global_key])
        if res["status"] != "SUCCESS":
            raise ResourceNotFoundError(
                Entity.DataRow, {global_key: global_key}
            )
        data_row_id = res["results"][0]

        return self.get_data_row(data_row_id)

    def get_data_row_metadata_ontology(self) -> DataRowMetadataOntology:
        """

        Returns:
            DataRowMetadataOntology: The ontology for Data Row Metadata for an organization

        """
        if self._data_row_metadata_ontology is None:
            self._data_row_metadata_ontology = DataRowMetadataOntology(self)
        return self._data_row_metadata_ontology

    def get_model(self, model_id) -> Model:
        """Gets a single Model with the given ID.

        >>> model = client.get_model("<model_id>")

        Args:
            model_id (str): Unique ID of the Model.
        Returns:
            The sought Model.
        Raises:
            ResourceNotFoundError: If there is no
                Model with the given ID.
        """
        return self._get_single(Entity.Model, model_id)

    def get_models(self, where=None) -> List[Model]:
        """Fetches all the models the user has access to.

        >>> models = client.get_models(where=(Model.name == "<model_name>"))

        Args:
            where (Comparison, LogicalOperation or None): The `where` clause
                for filtering.
        Returns:
            An iterable of Models (typically a PaginatedCollection).
        """
        return self._get_all(Entity.Model, where, filter_deleted=False)

    def create_model(self, name, ontology_id) -> Model:
        """Creates a Model object on the server.

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

        result = self.execute(
            query_str, {"name": name, "ontologyId": ontology_id}
        )
        return Entity.Model(self, result["createModel"])

    def get_data_row_ids_for_external_ids(
        self, external_ids: List[str]
    ) -> Dict[str, List[str]]:
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
                {"externalId_in": external_ids[i : i + max_ids_per_request]},
            )["externalIdsToDataRowIds"]:
                result[row["externalId"]].append(row["dataRowId"])
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
        params = {"search": name_contains, "filter": {"status": "ALL"}}
        return PaginatedCollection(
            self,
            query_str,
            params,
            ["ontologies", "nodes"],
            Entity.Ontology,
            ["ontologies", "nextCursor"],
        )

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
            {"rootSchemaNodeWhere": {"featureSchemaId": feature_schema_id}},
        )["rootSchemaNode"]
        res["id"] = res["normalized"]["featureSchemaId"]
        return Entity.FeatureSchema(self, res)

    def get_feature_schemas(self, name_contains) -> PaginatedCollection:
        """
        Fetches top level feature schemas with names that match the `name_contains` string

        Args:
            name_contains (str): search filter for a name of a root feature schema
                If present, results in a case insensitive 'like' search for feature schemas
                If None, returns all top level feature schemas
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
        params = {"search": name_contains, "filter": {"status": "ALL"}}

        def rootSchemaPayloadToFeatureSchema(client, payload):
            # Technically we are querying for a Schema Node.
            # But the features are the same so we just grab the feature schema id
            payload["id"] = payload["normalized"]["featureSchemaId"]
            return Entity.FeatureSchema(client, payload)

        return PaginatedCollection(
            self,
            query_str,
            params,
            ["rootSchemaNodes", "nodes"],
            rootSchemaPayloadToFeatureSchema,
            ["rootSchemaNodes", "nextCursor"],
        )

    def create_ontology_from_feature_schemas(
        self,
        name,
        feature_schema_ids,
        media_type: MediaType = None,
        ontology_kind: OntologyKind = None,
    ) -> Ontology:
        """
        Creates an ontology from a list of feature schema ids

        Args:
            name (str): Name of the ontology
            feature_schema_ids (List[str]): List of feature schema ids corresponding to
                top level tools and classifications to include in the ontology
            media_type (MediaType or None): Media type of a new ontology.
            ontology_kind (OntologyKind or None): set to OntologyKind.ModelEvaluation if the ontology is for chat evaluation,
                leave as None otherwise.
        Returns:
            The created Ontology

        NOTE for chat evaluation, we currently force media_type to Conversational and for response creation, we force media_type to Text.
        """
        tools, classifications = [], []
        for feature_schema_id in feature_schema_ids:
            feature_schema = self.get_feature_schema(feature_schema_id)
            tool = ["tool"]
            if "tool" in feature_schema.normalized:
                tool = feature_schema.normalized["tool"]
                try:
                    tool_type_cls = tool_type_cls_from_type(tool)
                    tool_type_cls(tool)
                    tools.append(feature_schema.normalized)
                except ValueError:
                    raise ValueError(
                        f"Tool `{tool}` not in list of supported tools."
                    )
            elif "type" in feature_schema.normalized:
                classification = feature_schema.normalized["type"]
                if (
                    classification
                    in Classification.Type._value2member_map_.keys()
                ):
                    Classification.Type(classification)
                    classifications.append(feature_schema.normalized)
                elif (
                    classification
                    in PromptResponseClassification.Type._value2member_map_.keys()
                ):
                    PromptResponseClassification.Type(classification)
                    classifications.append(feature_schema.normalized)
                else:
                    raise ValueError(
                        f"Classification `{classification}` not in list of supported classifications."
                    )
            else:
                raise ValueError(
                    "Neither `tool` or `classification` found in the normalized feature schema"
                )
        normalized = {"tools": tools, "classifications": classifications}

        # validation for ontology_kind and media_type is done within self.create_ontology
        return self.create_ontology(
            name=name,
            normalized=normalized,
            media_type=media_type,
            ontology_kind=ontology_kind,
        )

    def delete_unused_feature_schema(self, feature_schema_id: str) -> None:
        """
        Deletes a feature schema if it is not used by any ontologies or annotations
        Args:
            feature_schema_id (str): The id of the feature schema to delete
        Example:
            >>> client.delete_unused_feature_schema("cleabc1my012ioqvu5anyaabc")
        """

        endpoint = (
            self.rest_endpoint
            + "/feature-schemas/"
            + urllib.parse.quote(feature_schema_id)
        )
        response = self.connection.delete(endpoint)

        if response.status_code != requests.codes.no_content:
            raise LabelboxError(
                "Failed to delete the feature schema, message: "
                + str(response.json()["message"])
            )

    def delete_unused_ontology(self, ontology_id: str) -> None:
        """
        Deletes an ontology if it is not used by any annotations
        Args:
            ontology_id (str): The id of the ontology to delete
        Example:
            >>> client.delete_unused_ontology("cleabc1my012ioqvu5anyaabc")
        """
        endpoint = (
            self.rest_endpoint
            + "/ontologies/"
            + urllib.parse.quote(ontology_id)
        )
        response = self.connection.delete(endpoint)

        if response.status_code != requests.codes.no_content:
            raise LabelboxError(
                "Failed to delete the ontology, message: "
                + str(response.json()["message"])
            )

    def update_feature_schema_title(
        self, feature_schema_id: str, title: str
    ) -> FeatureSchema:
        """
        Updates a title of a feature schema
        Args:
            feature_schema_id (str): The id of the feature schema to update
            title (str): The new title of the feature schema
        Returns:
            The updated feature schema
        Example:
            >>> client.update_feature_schema_title("cleabc1my012ioqvu5anyaabc", "New Title")
        """

        endpoint = (
            self.rest_endpoint
            + "/feature-schemas/"
            + urllib.parse.quote(feature_schema_id)
            + "/definition"
        )
        response = self.connection.patch(endpoint, json={"title": title})

        if response.status_code == requests.codes.ok:
            return self.get_feature_schema(feature_schema_id)
        else:
            raise LabelboxError(
                "Failed to update the feature schema, message: "
                + str(response.json()["message"])
            )

    def upsert_feature_schema(self, feature_schema: Dict) -> FeatureSchema:
        """
        Upserts a feature schema
        Args:
            feature_schema: Dict representing the feature schema to upsert
        Returns:
            The upserted feature schema
        Example:
            Insert a new feature schema
            >>> tool = Tool(name="tool", tool=Tool.Type.BOUNDING_BOX, color="#FF0000")
            >>> client.upsert_feature_schema(tool.asdict())
            Update an existing feature schema
            >>> tool = Tool(feature_schema_id="cleabc1my012ioqvu5anyaabc", name="tool", tool=Tool.Type.BOUNDING_BOX, color="#FF0000")
            >>> client.upsert_feature_schema(tool.asdict())
        """

        feature_schema_id = (
            feature_schema.get("featureSchemaId") or "new_feature_schema_id"
        )
        endpoint = (
            self.rest_endpoint
            + "/feature-schemas/"
            + urllib.parse.quote(feature_schema_id)
        )
        response = self.connection.put(
            endpoint, json={"normalized": json.dumps(feature_schema)}
        )

        if response.status_code == requests.codes.ok:
            return self.get_feature_schema(response.json()["schemaId"])
        else:
            raise LabelboxError(
                "Failed to upsert the feature schema, message: "
                + str(response.json()["message"])
            )

    def insert_feature_schema_into_ontology(
        self, feature_schema_id: str, ontology_id: str, position: int
    ) -> None:
        """
        Inserts a feature schema into an ontology. If the feature schema is already in the ontology,
        it will be moved to the new position.
        Args:
            feature_schema_id (str): The feature schema id to upsert
            ontology_id (str): The id of the ontology to insert the feature schema into
            position (int): The position number of the feature schema in the ontology
        Example:
            >>> client.insert_feature_schema_into_ontology("cleabc1my012ioqvu5anyaabc", "clefdvwl7abcgefgu3lyvcde", 2)
        """

        endpoint = (
            self.rest_endpoint
            + "/ontologies/"
            + urllib.parse.quote(ontology_id)
            + "/feature-schemas/"
            + urllib.parse.quote(feature_schema_id)
        )
        response = self.connection.post(endpoint, json={"position": position})
        if response.status_code != requests.codes.created:
            raise LabelboxError(
                "Failed to insert the feature schema into the ontology, message: "
                + str(response.json()["message"])
            )

    def get_unused_ontologies(self, after: str = None) -> List[str]:
        """
        Returns a list of unused ontology ids
        Args:
            after (str): The cursor to use for pagination
        Returns:
            A list of unused ontology ids
        Example:
            To get the first page of unused ontology ids (100 at a time)
            >>> client.get_unused_ontologies()
            To get the next page of unused ontology ids
            >>> client.get_unused_ontologies("cleabc1my012ioqvu5anyaabc")
        """

        endpoint = self.rest_endpoint + "/ontologies/unused"
        response = self.connection.get(endpoint, json={"after": after})

        if response.status_code == requests.codes.ok:
            return response.json()
        else:
            raise LabelboxError(
                "Failed to get unused ontologies, message: "
                + str(response.json()["message"])
            )

    def get_unused_feature_schemas(self, after: str = None) -> List[str]:
        """
        Returns a list of unused feature schema ids
        Args:
            after (str): The cursor to use for pagination
        Returns:
            A list of unused feature schema ids
        Example:
            To get the first page of unused feature schema ids (100 at a time)
            >>> client.get_unused_feature_schemas()
            To get the next page of unused feature schema ids
            >>> client.get_unused_feature_schemas("cleabc1my012ioqvu5anyaabc")
        """

        endpoint = self.rest_endpoint + "/feature-schemas/unused"
        response = self.connection.get(endpoint, json={"after": after})

        if response.status_code == requests.codes.ok:
            return response.json()
        else:
            raise LabelboxError(
                "Failed to get unused feature schemas, message: "
                + str(response.json()["message"])
            )

    def create_ontology(
        self,
        name,
        normalized,
        media_type: MediaType = None,
        ontology_kind: OntologyKind = None,
    ) -> Ontology:
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
            ontology_kind (OntologyKind or None): set to OntologyKind.ModelEvaluation if the ontology is for chat evaluation or
                OntologyKind.ResponseCreation if ontology is for response creation, leave as None otherwise.

        Returns:
            The created Ontology

        NOTE for chat evaluation, we currently force media_type to Conversational and for response creation, we force media_type to Text.
        """

        media_type_value = None
        if media_type:
            if MediaType.is_supported(media_type):
                media_type_value = media_type.value
            else:
                raise get_media_type_validation_error(media_type)

        if ontology_kind and OntologyKind.is_supported(ontology_kind):
            media_type = OntologyKind.evaluate_ontology_kind_with_media_type(
                ontology_kind, media_type
            )
            editor_task_type_value = EditorTaskTypeMapper.to_editor_task_type(
                ontology_kind, media_type
            ).value
        elif ontology_kind:
            raise OntologyKind.get_ontology_kind_validation_error(ontology_kind)
        else:
            editor_task_type_value = None

        query_str = """mutation upsertRootSchemaNodePyApi($data:  UpsertOntologyInput!){
                           upsertOntology(data: $data){ %s }
        } """ % query.results_query_part(Entity.Ontology)
        params = {
            "data": {
                "name": name,
                "normalized": json.dumps(normalized),
                "mediaType": media_type_value,
            }
        }
        if editor_task_type_value:
            params["data"]["editorTaskType"] = editor_task_type_value

        res = self.execute(query_str, params)
        return Entity.Ontology(self, res["upsertOntology"])

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
                            name="name"
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
        params = {"data": {"normalized": json.dumps(normalized)}}
        res = self.execute(query_str, params)["upsertRootSchemaNode"]
        # Technically we are querying for a Schema Node.
        # But the features are the same so we just grab the feature schema id
        res["id"] = res["normalized"]["featureSchemaId"]
        return Entity.FeatureSchema(self, res)

    def get_model_run(self, model_run_id: str) -> ModelRun:
        """Gets a single ModelRun with the given ID.

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
        timeout_seconds=60,
    ) -> Dict[str, Union[str, List[Any]]]:
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

        def _format_successful_rows(
            rows: Dict[str, str], sanitized: bool
        ) -> List[Dict[str, str]]:
            return [
                {
                    "data_row_id": r["dataRowId"],
                    "global_key": r["globalKey"],
                    "sanitized": sanitized,
                }
                for r in rows
            ]

        def _format_failed_rows(
            rows: Dict[str, str], error_msg: str
        ) -> List[Dict[str, str]]:
            return [
                {
                    "data_row_id": r["dataRowId"],
                    "global_key": r["globalKey"],
                    "error": error_msg,
                }
                for r in rows
            ]

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
            "globalKeyDataRowLinks": [
                {utils.camel_case(key): value for key, value in input.items()}
                for input in global_key_to_data_row_inputs
            ]
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
            "jobId": assign_global_keys_to_data_rows_job[
                "assignGlobalKeysToDataRows"
            ]["jobId"]
        }

        # Poll job status until finished, then retrieve results
        sleep_time = 2
        start_time = time.time()
        while True:
            res = self.execute(result_query_str, result_params)
            if (
                res["assignGlobalKeysToDataRowsResult"]["jobStatus"]
                == "COMPLETE"
            ):
                results, errors = [], []
                res = res["assignGlobalKeysToDataRowsResult"]["data"]
                # Successful assignments
                results.extend(
                    _format_successful_rows(
                        rows=res["sanitizedAssignments"], sanitized=True
                    )
                )
                results.extend(
                    _format_successful_rows(
                        rows=res["unmodifiedAssignments"], sanitized=False
                    )
                )
                # Failed assignments
                errors.extend(
                    _format_failed_rows(
                        rows=res["invalidGlobalKeyAssignments"],
                        error_msg="Invalid assignment. Either DataRow does not exist, or globalKey is invalid",
                    )
                )
                errors.extend(
                    _format_failed_rows(
                        rows=res["accessDeniedAssignments"],
                        error_msg="Access denied to Data Row",
                    )
                )

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
            elif (
                res["assignGlobalKeysToDataRowsResult"]["jobStatus"] == "FAILED"
            ):
                raise LabelboxError(
                    "Job assign_global_keys_to_data_rows failed."
                )
            current_time = time.time()
            if current_time - start_time > timeout_seconds:
                raise TimeoutError(
                    "Timed out waiting for assign_global_keys_to_data_rows job to complete."
                )
            time.sleep(sleep_time)

    def get_data_row_ids_for_global_keys(
        self, global_keys: List[str], timeout_seconds=60
    ) -> Dict[str, Union[str, List[Any]]]:
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

        def _format_failed_rows(
            rows: List[str], error_msg: str
        ) -> List[Dict[str, str]]:
            return [{"global_key": r, "error": error_msg} for r in rows]

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
                } jobStatus}}
            """
        result_params = {
            "jobId": data_rows_for_global_keys_job["dataRowsForGlobalKeys"][
                "jobId"
            ]
        }

        # Poll job status until finished, then retrieve results
        sleep_time = 2
        start_time = time.time()
        while True:
            res = self.execute(result_query_str, result_params)
            if res["dataRowsForGlobalKeysResult"]["jobStatus"] == "COMPLETE":
                data = res["dataRowsForGlobalKeysResult"]["data"]
                results, errors = [], []
                results.extend([row["id"] for row in data["fetchedDataRows"]])
                errors.extend(
                    _format_failed_rows(
                        data["notFoundGlobalKeys"], "Data Row not found"
                    )
                )
                errors.extend(
                    _format_failed_rows(
                        data["accessDeniedGlobalKeys"],
                        "Access denied to Data Row",
                    )
                )

                # Invalid results may contain empty string, so we must filter
                # them prior to checking for PARTIAL_SUCCESS
                filtered_results = list(filter(lambda r: r != "", results))
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
            elif res["dataRowsForGlobalKeysResult"]["jobStatus"] == "FAILED":
                raise LabelboxError("Job dataRowsForGlobalKeys failed.")
            current_time = time.time()
            if current_time - start_time > timeout_seconds:
                raise TimeoutError(
                    "Timed out waiting for get_data_rows_for_global_keys job to complete."
                )
            time.sleep(sleep_time)

    def clear_global_keys(
        self, global_keys: List[str], timeout_seconds=60
    ) -> Dict[str, Union[str, List[Any]]]:
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
            >>> job_result = client.clear_global_keys(["key1","key2","notfoundkey"])
            >>> print(job_result['status'])
            Partial Success
            >>> print(job_result['results'])
            ['key1', 'key2']
            >>> print(job_result['errors'])
            [{'global_key': 'notfoundkey', 'error': 'Failed to find data row matching provided global key'}]
        """

        def _format_failed_rows(
            rows: List[str], error_msg: str
        ) -> List[Dict[str, str]]:
            return [{"global_key": r, "error": error_msg} for r in rows]

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
            if res["clearGlobalKeysResult"]["jobStatus"] == "COMPLETE":
                data = res["clearGlobalKeysResult"]["data"]
                results, errors = [], []
                results.extend(data["clearedGlobalKeys"])
                errors.extend(
                    _format_failed_rows(
                        data["failedToClearGlobalKeys"],
                        "Clearing global key failed",
                    )
                )
                errors.extend(
                    _format_failed_rows(
                        data["notFoundGlobalKeys"],
                        "Failed to find data row matching provided global key",
                    )
                )
                errors.extend(
                    _format_failed_rows(
                        data["accessDeniedGlobalKeys"],
                        "Denied access to modify data row matching provided global key",
                    )
                )

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
            elif res["clearGlobalKeysResult"]["jobStatus"] == "FAILED":
                raise LabelboxError("Job clearGlobalKeys failed.")
            current_time = time.time()
            if current_time - start_time > timeout_seconds:
                raise TimeoutError(
                    "Timed out waiting for clear_global_keys job to complete."
                )
            time.sleep(sleep_time)

    def get_catalog(self) -> Catalog:
        return Catalog(client=self)

    def get_catalog_slices(self) -> List[CatalogSlice]:
        """
        Fetches all slices of the given entity type.
        Returns:
            List[CatalogSlice]: A list of CatalogSlice objects.
        """
        query_str = """query GetCatalogSavedQueriesPyApi {
                catalogSavedQueries {
                    id
                    name
                    description
                    filter
                    createdAt
                    updatedAt
                }
            }
            """
        res = self.execute(query_str)
        return [CatalogSlice(self, sl) for sl in res["catalogSavedQueries"]]

    def get_catalog_slice(
        self, slice_id: Optional[str] = None, slice_name: Optional[str] = None
    ) -> Union[CatalogSlice, List[CatalogSlice]]:
        """
        Fetches a Slice using either the slice ID or the slice name.

        Args:
            slice_id (Optional[str]): The ID of the Slice.
            slice_name (Optional[str]): The name of the Slice.

        Returns:
            Union[CatalogSlice, List[CatalogSlice], ModelSlice, List[ModelSlice]]:
                The corresponding Slice object or list of Slice objects.

        Raises:
            ValueError: If neither or both id and name are provided.
            ResourceNotFoundError: If the slice is not found.
        """
        if (slice_id is None and slice_name is None) or (
            slice_id is not None and slice_name is not None
        ):
            raise ValueError("Provide exactly one of id or name")

        if slice_id is not None:
            query_str = """query getSavedQueryPyApi($id: ID!) {
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

            res = self.execute(query_str, {"id": slice_id})
            if res is None:
                raise ResourceNotFoundError(CatalogSlice, {"id": slice_id})

            return CatalogSlice(self, res["getSavedQuery"])

        else:
            slices = self.get_catalog_slices()
            matches = [s for s in slices if s.name == slice_name]

            if not matches:
                raise ResourceNotFoundError(CatalogSlice, {"name": slice_name})
            elif len(matches) > 1:
                return matches
            else:
                return matches[0]

    def is_feature_schema_archived(
        self, ontology_id: str, feature_schema_id: str
    ) -> bool:
        """
        Returns true if a feature schema is archived in the specified ontology, returns false otherwise.

        Args:
            feature_schema_id (str): The ID of the feature schema
            ontology_id (str): The ID of the ontology
        Returns:
            bool
        """

        ontology_endpoint = (
            self.rest_endpoint
            + "/ontologies/"
            + urllib.parse.quote(ontology_id)
        )
        response = self.connection.get(ontology_endpoint)

        if response.status_code == requests.codes.ok:
            feature_schema_nodes = response.json()["featureSchemaNodes"]
            tools = feature_schema_nodes["tools"]
            classifications = feature_schema_nodes["classifications"]
            relationships = feature_schema_nodes["relationships"]
            feature_schema_node_list = tools + classifications + relationships
            filtered_feature_schema_nodes = [
                feature_schema_node
                for feature_schema_node in feature_schema_node_list
                if feature_schema_node["featureSchemaId"] == feature_schema_id
            ]
            if filtered_feature_schema_nodes:
                return bool(filtered_feature_schema_nodes[0]["archived"])
            else:
                raise LabelboxError(
                    "The specified feature schema was not in the ontology."
                )

        elif response.status_code == 404:
            raise ResourceNotFoundError(Ontology, ontology_id)
        else:
            raise LabelboxError(
                "Failed to get the feature schema archived status."
            )

    def get_model_slice(self, slice_id) -> ModelSlice:
        """
        Fetches a Model Slice by ID.

        Args:
             slice_id (str): The ID of the Slice
        Returns:
            ModelSlice
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
        res = self.execute(query_str, {"id": slice_id})
        if res is None or res["getSavedQuery"] is None:
            raise ResourceNotFoundError(ModelSlice, slice_id)

        return Entity.ModelSlice(self, res["getSavedQuery"])

    def delete_feature_schema_from_ontology(
        self, ontology_id: str, feature_schema_id: str
    ) -> DeleteFeatureFromOntologyResult:
        """
        Deletes or archives a feature schema from an ontology.
        If the feature schema is a root level node with associated labels, it will be archived.
        If the feature schema is a nested node in the ontology and does not have associated labels, it will be deleted.
        If the feature schema is a nested node in the ontology and has associated labels, it will not be deleted.

        Args:
            ontology_id (str): The ID of the ontology.
            feature_schema_id (str): The ID of the feature schema.

        Returns:
            DeleteFeatureFromOntologyResult: The result of the feature schema removal.

        Example:
            >>> client.delete_feature_schema_from_ontology(<ontology_id>, <feature_schema_id>)
        """
        ontology_endpoint = (
            self.rest_endpoint
            + "/ontologies/"
            + urllib.parse.quote(ontology_id)
            + "/feature-schemas/"
            + urllib.parse.quote(feature_schema_id)
        )
        response = self.connection.delete(ontology_endpoint)

        if response.status_code == requests.codes.ok:
            response_json = response.json()
            if response_json["archived"] is True:
                logger.info(
                    "Feature schema was archived from the ontology because it had associated labels."
                )
            elif response_json["deleted"] is True:
                logger.info(
                    "Feature schema was successfully removed from the ontology"
                )
            result = DeleteFeatureFromOntologyResult()
            result.archived = bool(response_json["archived"])
            result.deleted = bool(response_json["deleted"])
            return result
        else:
            raise LabelboxError(
                "Failed to remove feature schema from ontology, message: "
                + str(response.json()["message"])
            )

    def unarchive_feature_schema_node(
        self, ontology_id: str, root_feature_schema_id: str
    ) -> None:
        """
        Unarchives a feature schema node in an ontology.
        Only root level feature schema nodes can be unarchived.
        Args:
            ontology_id (str): The ID of the ontology
            root_feature_schema_id (str): The ID of the root level feature schema
        Returns:
            None
        """
        ontology_endpoint = (
            self.rest_endpoint
            + "/ontologies/"
            + urllib.parse.quote(ontology_id)
            + "/feature-schemas/"
            + urllib.parse.quote(root_feature_schema_id)
            + "/unarchive"
        )
        response = self.connection.patch(ontology_endpoint)
        if response.status_code == requests.codes.ok:
            if not bool(response.json()["unarchived"]):
                raise LabelboxError("Failed unarchive the feature schema.")
        else:
            raise LabelboxError(
                "Failed unarchive the feature schema node, message: ",
                response.text,
            )

    def get_batch(self, project_id: str, batch_id: str) -> Entity.Batch:
        # obtain batch entity to return
        get_batch_str = """query %s($projectId: ID!, $batchId: ID!) {
                          project(where: {id: $projectId}) {
                             batches(where: {id: $batchId}) {
                                nodes {
                                   %s
                                }
                             }
                        }
                    }
                    """ % (
            "getProjectBatchPyApi",
            query.results_query_part(Entity.Batch),
        )

        batch = self.execute(
            get_batch_str,
            {"projectId": project_id, "batchId": batch_id},
            timeout=180.0,
        )["project"]["batches"]["nodes"][0]

        return Entity.Batch(self, project_id, batch)

    def send_to_annotate_from_catalog(
        self,
        destination_project_id: str,
        task_queue_id: Optional[str],
        batch_name: str,
        data_rows: Union[DataRowIds, GlobalKeys],
        params: Dict[str, Any],
    ):
        """
        Sends data rows from catalog to a specified project for annotation.

        Example usage:
            >>> task = client.send_to_annotate_from_catalog(
            >>>     destination_project_id=DESTINATION_PROJECT_ID,
            >>>     task_queue_id=TASK_QUEUE_ID,
            >>>     batch_name="batch_name",
            >>>     data_rows=UniqueIds([DATA_ROW_ID]),
            >>>     params={
            >>>         "source_project_id":
            >>>             SOURCE_PROJECT_ID,
            >>>         "override_existing_annotations_rule":
            >>>             ConflictResolutionStrategy.OverrideWithAnnotations
            >>>     })
            >>> task.wait_till_done()

        Args:
            destination_project_id: The ID of the project to send the data rows to.
            task_queue_id: The ID of the task queue to send the data rows to. If not specified, the data rows will be
                sent to the Done workflow state.
            batch_name: The name of the batch to create. If more than one batch is created, additional batches will be
                named with a monotonically increasing numerical suffix, starting at "_1".
            data_rows: The data rows to send to the project.
            params: Additional parameters to configure the job. See SendToAnnotateFromCatalogParams for more details.

        Returns: The created task for this operation.

        """

        validated_params = SendToAnnotateFromCatalogParams(**params)

        mutation_str = """mutation SendToAnnotateFromCatalogPyApi($input: SendToAnnotateFromCatalogInput!) {
                            sendToAnnotateFromCatalog(input: $input) {
                              taskId
                            }
                          }
        """

        destination_task_queue = build_destination_task_queue_input(
            task_queue_id
        )
        data_rows_query = self.build_catalog_query(data_rows)

        predictions_input = (
            build_predictions_input(
                validated_params.predictions_ontology_mapping,
                validated_params.source_model_run_id,
            )
            if validated_params.source_model_run_id
            else None
        )

        annotations_input = (
            build_annotations_input(
                validated_params.annotations_ontology_mapping,
                validated_params.source_project_id,
            )
            if validated_params.source_project_id
            else None
        )

        res = self.execute(
            mutation_str,
            {
                "input": {
                    "destinationProjectId": destination_project_id,
                    "batchInput": {
                        "batchName": batch_name,
                        "batchPriority": validated_params.batch_priority,
                    },
                    "destinationTaskQueue": destination_task_queue,
                    "excludeDataRowsInProject": validated_params.exclude_data_rows_in_project,
                    "annotationsInput": annotations_input,
                    "predictionsInput": predictions_input,
                    "conflictLabelsResolutionStrategy": validated_params.override_existing_annotations_rule,
                    "searchQuery": {"scope": None, "query": [data_rows_query]},
                    "ordering": {
                        "type": "RANDOM",
                        "random": {"seed": random.randint(0, 10000)},
                        "sorting": None,
                    },
                    "sorting": None,
                    "limit": None,
                }
            },
        )["sendToAnnotateFromCatalog"]

        return Entity.Task.get_task(self, res["taskId"])

    @staticmethod
    def build_catalog_query(data_rows: Union[DataRowIds, GlobalKeys]):
        """
        Given a list of data rows, builds a query that can be used to fetch the associated data rows from the catalog.

        Args:
            data_rows: A list of data rows. Can be either UniqueIds or GlobalKeys.

        Returns: A query that can be used to fetch the associated data rows from the catalog.

        """
        if isinstance(data_rows, DataRowIds):
            data_rows_query = {
                "type": "data_row_id",
                "operator": "is",
                "ids": list(data_rows),
            }
        elif isinstance(data_rows, GlobalKeys):
            data_rows_query = {
                "type": "global_key",
                "operator": "is",
                "ids": list(data_rows),
            }
        else:
            raise ValueError(
                f"Invalid data_rows type {type(data_rows)}. Type of data_rows must be DataRowIds or GlobalKey"
            )
        return data_rows_query

    def run_foundry_app(
        self,
        model_run_name: str,
        data_rows: Union[DataRowIds, GlobalKeys],
        app_id: str,
    ) -> Task:
        """
        Run a foundry app

        Args:
            model_run_name (str): Name of a new model run to store app predictions in
            data_rows (DataRowIds or GlobalKeys): Data row identifiers to run predictions on
            app_id (str): Foundry app to run predictions with
        """
        foundry_client = FoundryClient(self)
        return foundry_client.run_app(model_run_name, data_rows, app_id)

    def create_embedding(self, name: str, dims: int) -> Embedding:
        """
        Create a new embedding.  You must provide a name and the
        number of dimensions the embedding has.  Once an
        embedding has been created, you can upload the vector
        data associated with the embedding id.

        Args:
            name: The name of the embedding.
            dims: The number of dimensions.

        Returns:
            A new Embedding object.
        """
        data = self._adv_client.create_embedding(name, dims)
        return Embedding(self._adv_client, **data)

    def get_embeddings(self) -> List[Embedding]:
        """
        Return a list of all embeddings for the current organization.

        Returns:
            A list of embedding objects.
        """
        results = self._adv_client.get_embeddings()
        return [Embedding(self._adv_client, **data) for data in results]

    def get_embedding_by_id(self, id: str) -> Embedding:
        """
        Return the embedding for the provided embedding id.

        Args:
            id: The embedding ID.

        Returns:
            The embedding object.
        """
        data = self._adv_client.get_embedding(id)
        return Embedding(self._adv_client, **data)

    def get_embedding_by_name(self, name: str) -> Embedding:
        """
        Return the embedding for the provided embedding name.

        Args:
            name: The embedding name

        Returns:
            The embedding object.
        """
        # NB: It's safe to do the filtering client-side as we only allow 10 embeddings per org.
        embeddings = self.get_embeddings()
        for e in embeddings:
            if e.name == name:
                return e
        raise ResourceNotFoundError(Embedding, dict(name=name))

    def upsert_label_feedback(
        self, label_id: str, feedback: str, scores: Dict[str, float]
    ) -> List[LabelScore]:
        """
        Submits the label feedback which is a free-form text and numeric
        label scores.

        Args:
            label_id: Target label ID
            feedback: Free text comment regarding the label
            scores: A dict of scores, the key is a score name and the value is
            the score value

        Returns:
            A list of LabelScore instances
        """
        mutation_str = """
        mutation UpsertAutoQaLabelFeedbackPyApi(
            $labelId: ID!
            $feedback: String!
            $scores: Json!
            ) {
            upsertAutoQaLabelFeedback(
                input: {
                    labelId: $labelId,
                    feedback: $feedback,
                    scores: $scores
                    }
            ) {
                id
                scores {
                id
                name
                score
                }
            }
            }
        """
        res = self.execute(
            mutation_str,
            {"labelId": label_id, "feedback": feedback, "scores": scores},
        )
        scores_raw = res["upsertAutoQaLabelFeedback"]["scores"]

        return [
            LabelScore(name=x["name"], score=x["score"]) for x in scores_raw
        ]

    def get_labeling_service_dashboards(
        self,
        search_query: Optional[List[SearchFilter]] = None,
    ) -> PaginatedCollection:
        """
        Get all labeling service dashboards for a given org.

        Optional parameters:
        search_query: A list of search filters representing the search

        NOTE:
            - Retrieves all projects for the organization or as filtered by the search query
              - INCLUDING those not requesting labeling services
            - Sorted by project created date in ascending order.

        Examples:
            Retrieves all labeling service dashboards for a given workspace id:
            >>> workspace_filter = WorkspaceFilter(
            >>>     operation=OperationType.Workspace,
            >>>     operator=IdOperator.Is,
            >>>     values=[workspace_id])
            >>> labeling_service_dashboard = [
            >>>     ld for ld in project.client.get_labeling_service_dashboards(search_query=[workspace_filter])]

            Retrieves all labeling service dashboards requested less than 7 days ago:
            >>> seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            >>> workforce_requested_filter_before = WorkforceRequestedDateFilter(
            >>>     operation=OperationType.WorforceRequestedDate,
            >>>     value=DateValue(operator=RangeDateTimeOperatorWithSingleValue.GreaterThanOrEqual,
            >>>                     value=seven_days_ago))
            >>> labeling_service_dashboard = [ld for ld in project.client.get_labeling_service_dashboards(search_query=[workforce_requested_filter_before])]

            See libs/labelbox/src/labelbox/schema/search_filters.py and libs/labelbox/tests/unit/test_unit_search_filters.py for more examples.
        """
        return LabelingServiceDashboard.get_all(self, search_query=search_query)

    def get_task_by_id(self, task_id: str) -> Union[Task, DataUpsertTask]:
        """
        Fetches a task by ID.

        Args:
            task_id (str): The ID of the task.

        Returns:
            Task or DataUpsertTask

        Throws:
            ResourceNotFoundError: If the task does not exist.

        NOTE: Export task is not supported yet
        """
        user = self.get_user()
        query = """
            query GetUserCreatedTasksPyApi($userId: ID!, $taskId: ID!) {
            user(where: {id: $userId}) {
                createdTasks(where: {id: $taskId} skip: 0 first: 1) {
                    completionPercentage
                    createdAt
                    errors
                    metadata
                    name
                    result
                    status
                    type
                    id
                    updatedAt
                }
            }
        }
        """
        result = self.execute(query, {"userId": user.uid, "taskId": task_id})
        data = result.get("user", {}).get("createdTasks", [])
        if not data:
            raise ResourceNotFoundError(
                message=f"The task {task_id} does not exist."
            )
        task_data = data[0]
        if task_data["type"].lower() == "adv-upsert-data-rows":
            task = DataUpsertTask(self, task_data)
        else:
            task = Task(self, task_data)

        task._user = user
        return task

    def _get_cancelable_task_types(self):
        """Internal method that returns a list of task types that can be canceled.

        The result is cached after the first call to avoid unnecessary API requests.

        Returns:
            List[str]: List of cancelable task types in snake_case format
        """
        if self._cancelable_task_types is None:
            query = """query GetCancelableTaskTypesPyApi {
                cancelableTaskTypes
            }"""

            result = self.execute(query).get("cancelableTaskTypes", [])
            # Reformat to kebab case
            self._cancelable_task_types = [
                utils.snake_case(task_type).replace("_", "-")
                for task_type in result
            ]

        return self._cancelable_task_types

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancels a task with the given ID if the task type is cancelable and the task is in progress.

        Args:
            task_id (str): The ID of the task to cancel.

        Returns:
            bool: True if the task was successfully cancelled.

        Raises:
            LabelboxError: If the task could not be cancelled, if the task type is not cancelable,
                or if the task is not in progress.
            ResourceNotFoundError: If the task does not exist (raised by get_task_by_id).
        """
        # Get the task object to check its type and status
        task = self.get_task_by_id(task_id)

        # Check if task type is cancelable
        cancelable_types = self._get_cancelable_task_types()
        if task.type not in cancelable_types:
            raise LabelboxError(
                f"Task type '{task.type}' cannot be cancelled. Cancelable types are: {cancelable_types}"
            )

        # Check if task is in progress
        if task.status_as_enum != TaskStatus.In_Progress:
            raise LabelboxError(
                f"Task cannot be cancelled because it is not in progress. Current status: {task.status}"
            )

        mutation_str = """
        mutation CancelTaskPyApi($id: ID!) {
            cancelBulkOperationJob(id: $id) {
                success
            }
        }
        """
        res = self.execute(mutation_str, {"id": task_id})
        return res["cancelBulkOperationJob"]["success"]

    def create_api_key(
        self,
        name: str,
        user: Union[User, str],
        role: Union[Role, str],
        validity: int = 0,
        time_unit: TimeUnit = TimeUnit.SECOND,
        refresh_cache: bool = False,
    ) -> Dict[str, str]:
        """Creates a new API key.

        Args:
            name (str): The name of the API key.
            user (Union[User, str]): The user object or user ID to associate with the API key.
            role (Union[Role, str]): The role object or role ID to assign to the API key.
            validity (int, optional): The validity period of the API key. Defaults to 0 (no expiration).
            time_unit (TimeUnit, optional): The time unit for the validity period. Defaults to TimeUnit.SECOND.
            refresh_cache (bool, optional): Whether to refresh cached permissions and roles. Defaults to False.

        Returns:
            Dict[str, str]: A dictionary containing the created API key information.
        """
        warnings.warn(
            "The creation of API keys is currently in alpha and its behavior may change in future releases.",
        )
        if refresh_cache:
            # Clear cached attributes if they exist
            if hasattr(self, "_cached_current_user_permissions"):
                delattr(self, "_cached_current_user_permissions")
            if hasattr(self, "_cached_available_api_key_roles"):
                delattr(self, "_cached_available_api_key_roles")

        return ApiKey.create_api_key(
            self, name, user, role, validity, time_unit
        )

    def get_api_keys(self, include_expired: bool = False) -> List[ApiKey]:
        """Retrieves all API keys accessible to the current user.

        Args:
            include_revoked (bool, optional): Whether to include revoked API keys. Defaults to True.

        Returns:
            List[ApiKey]: A list of ApiKey objects.
        """
        return ApiKey.get_api_keys(self, include_expired)

    def get_api_key(self, api_key_id: str) -> Optional[ApiKey]:
        """Retrieves a single API key by its ID.

        Args:
            api_key_id (str): The unique ID of the API key.

        Returns:
            Optional[ApiKey]: The corresponding ApiKey object if found, otherwise None.
        """
        return ApiKey.get_api_key(self, api_key_id)
