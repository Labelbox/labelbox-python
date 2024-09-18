import json
import time
from uuid import UUID, uuid4
import functools

import logging
from pathlib import Path
from google.api_core import retry
from labelbox import parser
import requests
from pydantic import (
    ValidationError,
    BaseModel,
    Field,
    field_validator,
    model_validator,
    ConfigDict,
    StringConstraints,
)
from typing_extensions import Literal, Annotated
from typing import (
    Any,
    List,
    Optional,
    BinaryIO,
    Dict,
    Iterable,
    Tuple,
    Union,
    Type,
    Set,
    TYPE_CHECKING,
)

from labelbox import exceptions as lb_exceptions
from labelbox import utils
from labelbox.orm import query
from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Relationship
from labelbox.schema.enums import BulkImportRequestState
from labelbox.schema.serialization import serialize_labels
from labelbox.orm.model import Field as lb_Field

if TYPE_CHECKING:
    from labelbox import Project
    from labelbox.types import Label

NDJSON_MIME_TYPE = "application/x-ndjson"
logger = logging.getLogger(__name__)

# TODO: Deprecate this library in place of labelimport and malprediction import library.


def _determinants(parent_cls: Any) -> List[str]:
    return [
        k
        for k, v in parent_cls.model_fields.items()
        if v.json_schema_extra and "determinant" in v.json_schema_extra
    ]


def _make_file_name(project_id: str, name: str) -> str:
    return f"{project_id}__{name}.ndjson"


# TODO(gszpak): move it to client.py
def _make_request_data(
    project_id: str, name: str, content_length: int, file_name: str
) -> dict:
    query_str = """mutation createBulkImportRequestFromFilePyApi(
            $projectId: ID!, $name: String!, $file: Upload!, $contentLength: Int!) {
        createBulkImportRequest(data: {
            projectId: $projectId,
            name: $name,
            filePayload: {
                file: $file,
                contentLength: $contentLength
            }
        }) {
            %s
        }
    }
    """ % query.results_query_part(BulkImportRequest)
    variables = {
        "projectId": project_id,
        "name": name,
        "file": None,
        "contentLength": content_length,
    }
    operations = json.dumps({"variables": variables, "query": query_str})

    return {
        "operations": operations,
        "map": (None, json.dumps({file_name: ["variables.file"]})),
    }


def _send_create_file_command(
    client,
    request_data: dict,
    file_name: str,
    file_data: Tuple[str, Union[bytes, BinaryIO], str],
) -> dict:
    response = client.execute(data=request_data, files={file_name: file_data})

    if not response.get("createBulkImportRequest", None):
        raise lb_exceptions.LabelboxError(
            "Failed to create BulkImportRequest, message: %s"
            % response.get("errors", None)
            or response.get("error", None)
        )

    return response


class BulkImportRequest(DbObject):
    """Represents the import job when importing annotations.

    Attributes:
        name (str)
        state (Enum): FAILED, RUNNING, or FINISHED (Refers to the whole import job)
        input_file_url (str): URL to your web-hosted NDJSON file
        error_file_url (str): NDJSON that contains error messages for failed annotations
        status_file_url (str): NDJSON that contains status for each annotation
        created_at (datetime): UTC timestamp for date BulkImportRequest was created

        project (Relationship): `ToOne` relationship to Project
        created_by (Relationship): `ToOne` relationship to User
    """

    name = lb_Field.String("name")
    state = lb_Field.Enum(BulkImportRequestState, "state")
    input_file_url = lb_Field.String("input_file_url")
    error_file_url = lb_Field.String("error_file_url")
    status_file_url = lb_Field.String("status_file_url")
    created_at = lb_Field.DateTime("created_at")

    project = Relationship.ToOne("Project")
    created_by = Relationship.ToOne("User", False, "created_by")

    @property
    def inputs(self) -> List[Dict[str, Any]]:
        """
        Inputs for each individual annotation uploaded.
        This should match the ndjson annotations that you have uploaded.

        Returns:
            Uploaded ndjson.

        * This information will expire after 24 hours.
        """
        return self._fetch_remote_ndjson(self.input_file_url)

    @property
    def errors(self) -> List[Dict[str, Any]]:
        """
        Errors for each individual annotation uploaded. This is a subset of statuses

        Returns:
            List of dicts containing error messages. Empty list means there were no errors
            See `BulkImportRequest.statuses` for more details.

        * This information will expire after 24 hours.
        """
        self.wait_until_done()
        return self._fetch_remote_ndjson(self.error_file_url)

    @property
    def statuses(self) -> List[Dict[str, Any]]:
        """
        Status for each individual annotation uploaded.

        Returns:
            A status for each annotation if the upload is done running.
            See below table for more details

        .. list-table::
           :widths: 15 150
           :header-rows: 1

           * - Field
             - Description
           * - uuid
             - Specifies the annotation for the status row.
           * - dataRow
             - JSON object containing the Labelbox data row ID for the annotation.
           * - status
             - Indicates SUCCESS or FAILURE.
           * - errors
             - An array of error messages included when status is FAILURE. Each error has a name, message and optional (key might not exist) additional_info.

        * This information will expire after 24 hours.
        """
        self.wait_until_done()
        return self._fetch_remote_ndjson(self.status_file_url)

    @functools.lru_cache()
    def _fetch_remote_ndjson(self, url: str) -> List[Dict[str, Any]]:
        """
        Fetches the remote ndjson file and caches the results.

        Args:
            url (str): Can be any url pointing to an ndjson file.
        Returns:
            ndjson as a list of dicts.
        """
        response = requests.get(url)
        response.raise_for_status()
        return parser.loads(response.text)

    def refresh(self) -> None:
        """Synchronizes values of all fields with the database."""
        query_str, params = query.get_single(BulkImportRequest, self.uid)
        res = self.client.execute(query_str, params)
        res = res[utils.camel_case(BulkImportRequest.type_name())]
        self._set_field_values(res)

    def wait_till_done(self, sleep_time_seconds: int = 5) -> None:
        self.wait_until_done(sleep_time_seconds)

    def wait_until_done(self, sleep_time_seconds: int = 5) -> None:
        """Blocks import job until certain conditions are met.

        Blocks until the BulkImportRequest.state changes either to
        `BulkImportRequestState.FINISHED` or `BulkImportRequestState.FAILED`,
        periodically refreshing object's state.

        Args:
            sleep_time_seconds (str): a time to block between subsequent API calls
        """
        while self.state == BulkImportRequestState.RUNNING:
            logger.info(f"Sleeping for {sleep_time_seconds} seconds...")
            time.sleep(sleep_time_seconds)
            self.__exponential_backoff_refresh()

    @retry.Retry(
        predicate=retry.if_exception_type(
            lb_exceptions.ApiLimitError,
            lb_exceptions.TimeoutError,
            lb_exceptions.NetworkError,
        )
    )
    def __exponential_backoff_refresh(self) -> None:
        self.refresh()

    @classmethod
    def from_name(
        cls, client, project_id: str, name: str
    ) -> "BulkImportRequest":
        """Fetches existing BulkImportRequest.

        Args:
            client (Client): a Labelbox client
            project_id (str): BulkImportRequest's project id
            name (str): name of BulkImportRequest
        Returns:
            BulkImportRequest object

        """
        query_str = """query getBulkImportRequestPyApi(
                $projectId: ID!, $name: String!) {
            bulkImportRequest(where: {
                projectId: $projectId,
                name: $name
            }) {
                %s
            }
        }
        """ % query.results_query_part(cls)
        params = {"projectId": project_id, "name": name}
        response = client.execute(query_str, params=params)
        return cls(client, response["bulkImportRequest"])

    @classmethod
    def create_from_url(
        cls, client, project_id: str, name: str, url: str, validate=True
    ) -> "BulkImportRequest":
        """
        Creates a BulkImportRequest from a publicly accessible URL
        to an ndjson file with predictions.

        Args:
            client (Client): a Labelbox client
            project_id (str): id of project for which predictions will be imported
            name (str): name of BulkImportRequest
            url (str): publicly accessible URL pointing to ndjson file containing predictions
            validate (bool): a flag indicating if there should be a validation
                if `url` is valid ndjson
        Returns:
            BulkImportRequest object
        """
        if validate:
            logger.warn(
                "Validation is turned on. The file will be downloaded locally and processed before uploading."
            )
            res = requests.get(url)
            data = parser.loads(res.text)
            _validate_ndjson(data, client.get_project(project_id))

        query_str = """mutation createBulkImportRequestPyApi(
                $projectId: ID!, $name: String!, $fileUrl: String!) {
            createBulkImportRequest(data: {
                projectId: $projectId,
                name: $name,
                fileUrl: $fileUrl
            }) {
                %s
            }
        }
        """ % query.results_query_part(cls)
        params = {"projectId": project_id, "name": name, "fileUrl": url}
        bulk_import_request_response = client.execute(query_str, params=params)
        return cls(
            client, bulk_import_request_response["createBulkImportRequest"]
        )

    @classmethod
    def create_from_objects(
        cls,
        client,
        project_id: str,
        name: str,
        predictions: Union[Iterable[Dict], Iterable["Label"]],
        validate=True,
    ) -> "BulkImportRequest":
        """
        Creates a `BulkImportRequest` from an iterable of dictionaries.

        Conforms to JSON predictions format, e.g.:
        ``{
            "uuid": "9fd9a92e-2560-4e77-81d4-b2e955800092",
            "schemaId": "ckappz7d700gn0zbocmqkwd9i",
            "dataRow": {
                "id": "ck1s02fqxm8fi0757f0e6qtdc"
            },
            "bbox": {
                "top": 48,
                "left": 58,
                "height": 865,
                "width": 1512
            }
        }``

        Args:
            client (Client): a Labelbox client
            project_id (str): id of project for which predictions will be imported
            name (str): name of BulkImportRequest
            predictions (Iterable[dict]): iterable of dictionaries representing predictions
            validate (bool): a flag indicating if there should be a validation
                if `predictions` is valid ndjson
        Returns:
            BulkImportRequest object
        """
        if not isinstance(predictions, list):
            raise TypeError(
                f"annotations must be in a form of Iterable. Found {type(predictions)}"
            )
        ndjson_predictions = serialize_labels(predictions)

        if validate:
            _validate_ndjson(ndjson_predictions, client.get_project(project_id))

        data_str = parser.dumps(ndjson_predictions)
        if not data_str:
            raise ValueError("annotations cannot be empty")

        data = data_str.encode("utf-8")
        file_name = _make_file_name(project_id, name)
        request_data = _make_request_data(
            project_id, name, len(data_str), file_name
        )
        file_data = (file_name, data, NDJSON_MIME_TYPE)
        response_data = _send_create_file_command(
            client,
            request_data=request_data,
            file_name=file_name,
            file_data=file_data,
        )

        return cls(client, response_data["createBulkImportRequest"])

    @classmethod
    def create_from_local_file(
        cls, client, project_id: str, name: str, file: Path, validate_file=True
    ) -> "BulkImportRequest":
        """
        Creates a BulkImportRequest from a local ndjson file with predictions.

        Args:
            client (Client): a Labelbox client
            project_id (str): id of project for which predictions will be imported
            name (str): name of BulkImportRequest
            file (Path): local ndjson file with predictions
            validate_file (bool): a flag indicating if there should be a validation
                if `file` is a valid ndjson file
        Returns:
            BulkImportRequest object

        """
        file_name = _make_file_name(project_id, name)
        content_length = file.stat().st_size
        request_data = _make_request_data(
            project_id, name, content_length, file_name
        )

        with file.open("rb") as f:
            if validate_file:
                reader = parser.reader(f)
                # ensure that the underlying json load call is valid
                # https://github.com/rhgrant10/ndjson/blob/ff2f03c56b21f28f7271b27da35ca4a8bf9a05d0/ndjson/api.py#L53
                # by iterating through the file so we only store
                # each line in memory rather than the entire file
                try:
                    _validate_ndjson(reader, client.get_project(project_id))
                except ValueError:
                    raise ValueError(f"{file} is not a valid ndjson file")
                else:
                    f.seek(0)
            file_data = (file.name, f, NDJSON_MIME_TYPE)
            response_data = _send_create_file_command(
                client, request_data, file_name, file_data
            )
        return cls(client, response_data["createBulkImportRequest"])

    def delete(self) -> None:
        """Deletes the import job and also any annotations created by this import.

        Returns:
            None
        """
        id_param = "bulk_request_id"
        query_str = """mutation deleteBulkImportRequestPyApi($%s: ID!) {
            deleteBulkImportRequest(where: {id: $%s}) {
                id
                name
            }
        }""" % (id_param, id_param)
        self.client.execute(query_str, {id_param: self.uid})


def _validate_ndjson(
    lines: Iterable[Dict[str, Any]], project: "Project"
) -> None:
    """
    Client side validation of an ndjson object.

    Does not guarentee that an upload will succeed for the following reasons:
        * We are not checking the data row types which will cause the following errors to slip through
            * Missing frame indices will not causes an error for videos
        * Uploaded annotations for the wrong data type will pass (Eg. entity on images)
        * We are not checking bounds of an asset (Eg. frame index, image height, text location)

    Args:
        lines (Iterable[Dict[str,Any]]): An iterable of ndjson lines
        project (Project): id of project for which predictions will be imported

    Raises:
        MALValidationError: Raise for invalid NDJson
        UuidError: Duplicate UUID in upload
    """
    feature_schemas_by_id, feature_schemas_by_name = get_mal_schemas(
        project.ontology()
    )
    uids: Set[str] = set()
    for idx, line in enumerate(lines):
        try:
            annotation = NDAnnotation(**line)
            annotation.validate_instance(
                feature_schemas_by_id, feature_schemas_by_name
            )
            uuid = str(annotation.uuid)
            if uuid in uids:
                raise lb_exceptions.UuidError(
                    f"{uuid} already used in this import job, "
                    "must be unique for the project."
                )
            uids.add(uuid)
        except (ValidationError, ValueError, TypeError, KeyError) as e:
            raise lb_exceptions.MALValidationError(
                f"Invalid NDJson on line {idx}"
            ) from e


# The rest of this file contains objects for MAL validation
def parse_classification(tool):
    """
    Parses a classification from an ontology. Only radio, checklist, and text are supported for mal

    Args:
        tool (dict)

    Returns:
        dict
    """
    if tool["type"] in ["radio", "checklist"]:
        option_schema_ids = [r["featureSchemaId"] for r in tool["options"]]
        option_names = [r["value"] for r in tool["options"]]
        return {
            "tool": tool["type"],
            "featureSchemaId": tool["featureSchemaId"],
            "name": tool["name"],
            "options": [*option_schema_ids, *option_names],
        }
    elif tool["type"] == "text":
        return {
            "tool": tool["type"],
            "name": tool["name"],
            "featureSchemaId": tool["featureSchemaId"],
        }


def get_mal_schemas(ontology):
    """
    Converts a project ontology to a dict for easier lookup during ndjson validation

    Args:
        ontology (Ontology)
    Returns:
        Dict, Dict : Useful for looking up a tool from a given feature schema id or name
    """

    valid_feature_schemas_by_schema_id = {}
    valid_feature_schemas_by_name = {}
    for tool in ontology.normalized["tools"]:
        classifications = [
            parse_classification(classification_tool)
            for classification_tool in tool["classifications"]
        ]
        classifications_by_schema_id = {
            v["featureSchemaId"]: v for v in classifications
        }
        classifications_by_name = {v["name"]: v for v in classifications}
        valid_feature_schemas_by_schema_id[tool["featureSchemaId"]] = {
            "tool": tool["tool"],
            "classificationsBySchemaId": classifications_by_schema_id,
            "classificationsByName": classifications_by_name,
            "name": tool["name"],
        }
        valid_feature_schemas_by_name[tool["name"]] = {
            "tool": tool["tool"],
            "classificationsBySchemaId": classifications_by_schema_id,
            "classificationsByName": classifications_by_name,
            "name": tool["name"],
        }
    for tool in ontology.normalized["classifications"]:
        valid_feature_schemas_by_schema_id[tool["featureSchemaId"]] = (
            parse_classification(tool)
        )
        valid_feature_schemas_by_name[tool["name"]] = parse_classification(tool)
    return valid_feature_schemas_by_schema_id, valid_feature_schemas_by_name


class Bbox(BaseModel):
    top: float
    left: float
    height: float
    width: float


class Point(BaseModel):
    x: float
    y: float


class FrameLocation(BaseModel):
    end: int
    start: int


class VideoSupported(BaseModel):
    # Note that frames are only allowed as top level inferences for video
    frames: Optional[List[FrameLocation]] = None


# Base class for a special kind of union.
class SpecialUnion:
    def __new__(cls, **kwargs):
        return cls.build(kwargs)

    @classmethod
    def __get_validators__(cls):
        yield cls.build

    @classmethod
    def get_union_types(cls):
        if not issubclass(cls, SpecialUnion):
            raise TypeError("{} must be a subclass of SpecialUnion")

        union_types = [x for x in cls.__orig_bases__ if hasattr(x, "__args__")]
        if len(union_types) < 1:
            raise TypeError(
                "Class {cls} should inherit from a union of objects to build"
            )
        if len(union_types) > 1:
            raise TypeError(
                f"Class {cls} should inherit from exactly one union of objects to build. Found {union_types}"
            )
        return union_types[0].__args__[0].__args__

    @classmethod
    def build(cls: Any, data: Union[dict, BaseModel]) -> "NDBase":
        """
        Checks through all objects in the union to see which matches the input data.
        Args:
            data  (Union[dict, BaseModel]) : The data for constructing one of the objects in the union
        raises:
            KeyError: data does not contain the determinant fields for any of the types supported by this SpecialUnion
            ValidationError: Error while trying to construct a specific object in the union

        """
        if isinstance(data, BaseModel):
            data = data.model_dump()

        top_level_fields = []
        max_match = 0
        matched = None

        for type_ in cls.get_union_types():
            determinate_fields = _determinants(type_)
            top_level_fields.append(determinate_fields)
            matches = sum([val in determinate_fields for val in data])
            if matches == len(determinate_fields) and matches > max_match:
                max_match = matches
                matched = type_

        if matched is not None:
            # These two have the exact same top level keys
            if matched in [NDRadio, NDText]:
                if isinstance(data["answer"], dict):
                    matched = NDRadio
                elif isinstance(data["answer"], str):
                    matched = NDText
                else:
                    raise TypeError(
                        f"Unexpected type for answer field. Found {data['answer']}. Expected a string or a dict"
                    )
            return matched(**data)
        else:
            raise KeyError(
                f"Invalid annotation. Must have one of the following keys : {top_level_fields}. Found {data}."
            )

    @classmethod
    def schema(cls):
        results = {"definitions": {}}
        for cl in cls.get_union_types():
            schema = cl.schema()
            results["definitions"].update(schema.pop("definitions"))
            results[cl.__name__] = schema
        return results


class DataRow(BaseModel):
    id: str


class NDFeatureSchema(BaseModel):
    schemaId: Optional[str] = None
    name: Optional[str] = None

    @model_validator(mode="after")
    def most_set_one(self):
        if self.schemaId is None and self.name is None:
            raise ValueError(
                "Must set either schemaId or name for all feature schemas"
            )
        return self


class NDBase(NDFeatureSchema):
    ontology_type: str
    uuid: UUID
    dataRow: DataRow
    model_config = ConfigDict(extra="forbid")

    def validate_feature_schemas(
        self, valid_feature_schemas_by_id, valid_feature_schemas_by_name
    ):
        if self.name:
            if self.name not in valid_feature_schemas_by_name:
                raise ValueError(
                    f"Name {self.name} is not valid for the provided project's ontology."
                )

            if (
                self.ontology_type
                != valid_feature_schemas_by_name[self.name]["tool"]
            ):
                raise ValueError(
                    f"Name {self.name} does not map to the assigned tool {valid_feature_schemas_by_name[self.name]['tool']}"
                )

        if self.schemaId:
            if self.schemaId not in valid_feature_schemas_by_id:
                raise ValueError(
                    f"Schema id {self.schemaId} is not valid for the provided project's ontology."
                )

            if (
                self.ontology_type
                != valid_feature_schemas_by_id[self.schemaId]["tool"]
            ):
                raise ValueError(
                    f"Schema id {self.schemaId} does not map to the assigned tool {valid_feature_schemas_by_id[self.schemaId]['tool']}"
                )

    def validate_instance(
        self, valid_feature_schemas_by_id, valid_feature_schemas_by_name
    ):
        self.validate_feature_schemas(
            valid_feature_schemas_by_id, valid_feature_schemas_by_name
        )


###### Classifications ######


class NDText(NDBase):
    ontology_type: Literal["text"] = "text"
    answer: str = Field(json_schema_extra={"determinant": True})
    # No feature schema to check


class NDChecklist(VideoSupported, NDBase):
    ontology_type: Literal["checklist"] = "checklist"
    answers: List[NDFeatureSchema] = Field(
        json_schema_extra={"determinant": True}
    )

    @field_validator("answers", mode="before")
    def validate_answers(cls, value, field):
        # constr not working with mypy.
        if not len(value):
            raise ValueError("Checklist answers should not be empty")
        return value

    def validate_feature_schemas(
        self, valid_feature_schemas_by_id, valid_feature_schemas_by_name
    ):
        # Test top level feature schema for this tool
        super(NDChecklist, self).validate_feature_schemas(
            valid_feature_schemas_by_id, valid_feature_schemas_by_name
        )
        # Test the feature schemas provided to the answer field
        if len(
            set([answer.name or answer.schemaId for answer in self.answers])
        ) != len(self.answers):
            raise ValueError(
                f"Duplicated featureSchema found for checklist {self.uuid}"
            )
        for answer in self.answers:
            options = (
                valid_feature_schemas_by_name[self.name]["options"]
                if self.name
                else valid_feature_schemas_by_id[self.schemaId]["options"]
            )
            if answer.name not in options and answer.schemaId not in options:
                raise ValueError(
                    f"Feature schema provided to {self.ontology_type} invalid. Expected on of {options}. Found {answer}"
                )


class NDRadio(VideoSupported, NDBase):
    ontology_type: Literal["radio"] = "radio"
    answer: NDFeatureSchema = Field(json_schema_extra={"determinant": True})

    def validate_feature_schemas(
        self, valid_feature_schemas_by_id, valid_feature_schemas_by_name
    ):
        super(NDRadio, self).validate_feature_schemas(
            valid_feature_schemas_by_id, valid_feature_schemas_by_name
        )
        options = (
            valid_feature_schemas_by_name[self.name]["options"]
            if self.name
            else valid_feature_schemas_by_id[self.schemaId]["options"]
        )
        if (
            self.answer.name not in options
            and self.answer.schemaId not in options
        ):
            raise ValueError(
                f"Feature schema provided to {self.ontology_type} invalid. Expected on of {options}. Found {self.answer.name or self.answer.schemaId}"
            )


# A union with custom construction logic to improve error messages
class NDClassification(
    SpecialUnion,
    Type[Union[NDText, NDRadio, NDChecklist]],  # type: ignore
): ...


###### Tools ######


class NDBaseTool(NDBase):
    classifications: List[NDClassification] = []

    # This is indepdent of our problem
    def validate_feature_schemas(
        self, valid_feature_schemas_by_id, valid_feature_schemas_by_name
    ):
        super(NDBaseTool, self).validate_feature_schemas(
            valid_feature_schemas_by_id, valid_feature_schemas_by_name
        )
        for classification in self.classifications:
            classification.validate_feature_schemas(
                valid_feature_schemas_by_name[self.name][
                    "classificationsBySchemaId"
                ]
                if self.name
                else valid_feature_schemas_by_id[self.schemaId][
                    "classificationsBySchemaId"
                ],
                valid_feature_schemas_by_name[self.name][
                    "classificationsByName"
                ]
                if self.name
                else valid_feature_schemas_by_id[self.schemaId][
                    "classificationsByName"
                ],
            )

    @field_validator("classifications", mode="before")
    def validate_subclasses(cls, value, field):
        # Create uuid and datarow id so we don't have to define classification objects twice
        # This is caused by the fact that we require these ids for top level classifications but not for subclasses
        results = []
        dummy_id = "child".center(25, "_")
        for row in value:
            results.append(
                {**row, "dataRow": {"id": dummy_id}, "uuid": str(uuid4())}
            )
        return results


class NDPolygon(NDBaseTool):
    ontology_type: Literal["polygon"] = "polygon"
    polygon: List[Point] = Field(json_schema_extra={"determinant": True})

    @field_validator("polygon")
    def is_geom_valid(cls, v):
        if len(v) < 3:
            raise ValueError(
                f"A polygon must have at least 3 points to be valid. Found {v}"
            )
        return v


class NDPolyline(NDBaseTool):
    ontology_type: Literal["line"] = "line"
    line: List[Point] = Field(json_schema_extra={"determinant": True})

    @field_validator("line")
    def is_geom_valid(cls, v):
        if len(v) < 2:
            raise ValueError(
                f"A line must have at least 2 points to be valid. Found {v}"
            )
        return v


class NDRectangle(NDBaseTool):
    ontology_type: Literal["rectangle"] = "rectangle"
    bbox: Bbox = Field(json_schema_extra={"determinant": True})
    # Could check if points are positive


class NDPoint(NDBaseTool):
    ontology_type: Literal["point"] = "point"
    point: Point = Field(json_schema_extra={"determinant": True})
    # Could check if points are positive


class EntityLocation(BaseModel):
    start: int
    end: int


class NDTextEntity(NDBaseTool):
    ontology_type: Literal["named-entity"] = "named-entity"
    location: EntityLocation = Field(json_schema_extra={"determinant": True})

    @field_validator("location")
    def is_valid_location(cls, v):
        if isinstance(v, BaseModel):
            v = v.model_dump()

        if len(v) < 2:
            raise ValueError(
                f"A line must have at least 2 points to be valid. Found {v}"
            )
        if v["start"] < 0:
            raise ValueError(f"Text location must be positive. Found {v}")
        if v["start"] > v["end"]:
            raise ValueError(
                f"Text start location must be less or equal than end. Found {v}"
            )
        return v


class RLEMaskFeatures(BaseModel):
    counts: List[int]
    size: List[int]

    @field_validator("counts")
    def validate_counts(cls, counts):
        if not all([count >= 0 for count in counts]):
            raise ValueError(
                "Found negative value for counts. They should all be zero or positive"
            )
        return counts

    @field_validator("size")
    def validate_size(cls, size):
        if len(size) != 2:
            raise ValueError(
                f"Mask `size` should have two ints representing height and with. Found : {size}"
            )
        if not all([count > 0 for count in size]):
            raise ValueError(
                f"Mask `size` should be a postitive int. Found : {size}"
            )
        return size


class PNGMaskFeatures(BaseModel):
    # base64 encoded png bytes
    png: str


class URIMaskFeatures(BaseModel):
    instanceURI: str
    colorRGB: Union[List[int], Tuple[int, int, int]]

    @field_validator("colorRGB")
    def validate_color(cls, colorRGB):
        # Does the dtype matter? Can it be a float?
        if not isinstance(colorRGB, (tuple, list)):
            raise ValueError(
                f"Received color that is not a list or tuple. Found : {colorRGB}"
            )
        elif len(colorRGB) != 3:
            raise ValueError(
                f"Must provide RGB values for segmentation colors. Found : {colorRGB}"
            )
        elif not all([0 <= color <= 255 for color in colorRGB]):
            raise ValueError(
                f"All rgb colors must be between 0 and 255. Found : {colorRGB}"
            )
        return colorRGB


class NDMask(NDBaseTool):
    ontology_type: Literal["superpixel"] = "superpixel"
    mask: Union[URIMaskFeatures, PNGMaskFeatures, RLEMaskFeatures] = Field(
        json_schema_extra={"determinant": True}
    )


# A union with custom construction logic to improve error messages
class NDTool(
    SpecialUnion,
    Type[  # type: ignore
        Union[
            NDMask,
            NDTextEntity,
            NDPoint,
            NDRectangle,
            NDPolyline,
            NDPolygon,
        ]
    ],
): ...


class NDAnnotation(
    SpecialUnion,
    Type[Union[NDTool, NDClassification]],  # type: ignore
):
    @classmethod
    def build(cls: Any, data) -> "NDBase":
        if not isinstance(data, dict):
            raise ValueError("value must be dict")
        errors = []
        for cl in cls.get_union_types():
            try:
                return cl(**data)
            except KeyError as e:
                errors.append(f"{cl.__name__}: {e}")

        raise ValueError(
            "Unable to construct any annotation.\n{}".format("\n".join(errors))
        )

    @classmethod
    def schema(cls):
        data = {"definitions": {}}
        for type_ in cls.get_union_types():
            schema_ = type_.schema()
            data["definitions"].update(schema_.pop("definitions"))
            data[type_.__name__] = schema_
        return data
