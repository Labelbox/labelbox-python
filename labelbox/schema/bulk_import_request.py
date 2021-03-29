import json
import time
from uuid import UUID, uuid4
import functools

import logging
from pathlib import Path
import pydantic
import backoff
import ndjson
import requests
from pydantic import BaseModel, validator
from requests.api import request
from typing_extensions import Literal
from typing import (Any, List, Optional, BinaryIO, Dict, Iterable, Tuple, Union,
                    Type, Set)

import labelbox
from labelbox import utils
from labelbox.orm import query
from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field, Relationship
from labelbox.schema.enums import BulkImportRequestState

NDJSON_MIME_TYPE = "application/x-ndjson"
logger = logging.getLogger(__name__)


def _make_file_name(project_id: str, name: str) -> str:
    return f"{project_id}__{name}.ndjson"


# TODO(gszpak): move it to client.py
def _make_request_data(project_id: str, name: str, content_length: int,
                       file_name: str) -> dict:
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
        "contentLength": content_length
    }
    operations = json.dumps({"variables": variables, "query": query_str})

    return {
        "operations": operations,
        "map": (None, json.dumps({file_name: ["variables.file"]}))
    }


# TODO(gszpak): move it to client.py
def _send_create_file_command(
        client, request_data: dict, file_name: str,
        file_data: Tuple[str, Union[bytes, BinaryIO], str]) -> dict:
    response = requests.post(
        client.endpoint,
        headers={"authorization": "Bearer %s" % client.api_key},
        data=request_data,
        files={file_name: file_data})

    try:
        response_json = response.json()
    except ValueError:
        raise labelbox.exceptions.LabelboxError(
            "Failed to parse response as JSON: %s" % response.text)

    response_data = response_json.get("data", None)
    if response_data is None:
        raise labelbox.exceptions.LabelboxError(
            "Failed to upload, message: %s" % response_json.get("errors", None))

    if not response_data.get("createBulkImportRequest", None):
        raise labelbox.exceptions.LabelboxError(
            "Failed to create BulkImportRequest, message: %s" %
            response_json.get("errors", None) or
            response_data.get("error", None))

    return response_data


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
    name = Field.String("name")
    state = Field.Enum(BulkImportRequestState, "state")
    input_file_url = Field.String("input_file_url")
    error_file_url = Field.String("error_file_url")
    status_file_url = Field.String("status_file_url")
    created_at = Field.DateTime("created_at")

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
        return ndjson.loads(response.text)

    def refresh(self) -> None:
        """Synchronizes values of all fields with the database.
        """
        query_str, params = query.get_single(BulkImportRequest, self.uid)
        res = self.client.execute(query_str, params)
        res = res[utils.camel_case(BulkImportRequest.type_name())]
        self._set_field_values(res)

    def wait_until_done(self, sleep_time_seconds: int = 30) -> None:
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

    @backoff.on_exception(
        backoff.expo,
        (labelbox.exceptions.ApiLimitError, labelbox.exceptions.TimeoutError,
         labelbox.exceptions.NetworkError),
        max_tries=10,
        jitter=None)
    def __exponential_backoff_refresh(self) -> None:
        self.refresh()

    @classmethod
    def from_name(cls, client, project_id: str,
                  name: str) -> 'BulkImportRequest':
        """ Fetches existing BulkImportRequest.

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
        return cls(client, response['bulkImportRequest'])

    @classmethod
    def create_from_url(cls,
                        client,
                        project_id: str,
                        name: str,
                        url: str,
                        validate=True) -> 'BulkImportRequest':
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
            data = ndjson.loads(res.text)
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
        return cls(client,
                   bulk_import_request_response["createBulkImportRequest"])

    @classmethod
    def create_from_objects(cls,
                            client,
                            project_id: str,
                            name: str,
                            predictions: Iterable[Dict],
                            validate=True) -> 'BulkImportRequest':
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
        if validate:
            _validate_ndjson(predictions, client.get_project(project_id))

        data_str = ndjson.dumps(predictions)
        if not data_str:
            raise ValueError('annotations cannot be empty')

        data = data_str.encode('utf-8')
        file_name = _make_file_name(project_id, name)
        request_data = _make_request_data(project_id, name, len(data_str),
                                          file_name)
        file_data = (file_name, data, NDJSON_MIME_TYPE)
        response_data = _send_create_file_command(client,
                                                  request_data=request_data,
                                                  file_name=file_name,
                                                  file_data=file_data)

        return cls(client, response_data["createBulkImportRequest"])

    @classmethod
    def create_from_local_file(cls,
                               client,
                               project_id: str,
                               name: str,
                               file: Path,
                               validate_file=True) -> 'BulkImportRequest':
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
        request_data = _make_request_data(project_id, name, content_length,
                                          file_name)

        with file.open('rb') as f:
            if validate_file:
                reader = ndjson.reader(f)
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
            response_data = _send_create_file_command(client, request_data,
                                                      file_name, file_data)
        return cls(client, response_data["createBulkImportRequest"])


def _validate_ndjson(lines: Iterable[Dict[str, Any]],
                     project: "labelbox.Project") -> None:
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
    data_row_ids = {
        data_row.uid: data_row for dataset in project.datasets()
        for data_row in dataset.data_rows()
    }
    feature_schemas = get_mal_schemas(project.ontology())
    uids: Set[str] = set()
    for idx, line in enumerate(lines):
        try:
            annotation = NDAnnotation(**line)
            annotation.validate_instance(data_row_ids, feature_schemas)
            uuid = str(annotation.uuid)
            if uuid in uids:
                raise labelbox.exceptions.UuidError(
                    f'{uuid} already used in this import job, '
                    'must be unique for the project.')
            uids.add(uuid)
        except (pydantic.ValidationError, ValueError, TypeError, KeyError) as e:
            raise labelbox.exceptions.MALValidationError(
                f"Invalid NDJson on line {idx}") from e


#The rest of this file contains objects for MAL validation
def parse_classification(tool):
    """
    Parses a classification from an ontology. Only radio, checklist, and text are supported for mal

    Args:
        tool (dict)

    Returns:
        dict
    """
    if tool['type'] in ['radio', 'checklist']:
        return {
            'tool': tool['type'],
            'featureSchemaId': tool['featureSchemaId'],
            'options': [r['featureSchemaId'] for r in tool['options']]
        }
    elif tool['type'] == 'text':
        return {
            'tool': tool['type'],
            'featureSchemaId': tool['featureSchemaId']
        }


def get_mal_schemas(ontology):
    """
    Converts a project ontology to a dict for easier lookup during ndjson validation

    Args:
        ontology (Ontology)
    Returns:
        Dict : Useful for looking up a tool from a given feature schema id
    """

    valid_feature_schemas = {}
    for tool in ontology.normalized['tools']:
        classifications = [
            parse_classification(classification_tool)
            for classification_tool in tool['classifications']
        ]
        classifications = {v['featureSchemaId']: v for v in classifications}
        valid_feature_schemas[tool['featureSchemaId']] = {
            'tool': tool['tool'],
            'classifications': classifications
        }
    for tool in ontology.normalized['classifications']:
        valid_feature_schemas[tool['featureSchemaId']] = parse_classification(
            tool)
    return valid_feature_schemas


LabelboxID: str = pydantic.Field(..., min_length=25, max_length=25)


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
    #Note that frames are only allowed as top level inferences for video
    frames: Optional[List[FrameLocation]]


#Base class for a special kind of union.
# Compatible with pydantic. Improves error messages over a traditional union
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
                "Class {cls} should inherit from a union of objects to build")
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
            data = data.dict()

        top_level_fields = []
        max_match = 0
        matched = None

        for type_ in cls.get_union_types():
            determinate_fields = type_.Config.determinants(type_)
            top_level_fields.append(determinate_fields)
            matches = sum([val in determinate_fields for val in data])
            if matches == len(determinate_fields) and matches > max_match:
                max_match = matches
                matched = type_

        if matched is not None:
            #These two have the exact same top level keys
            if matched in [NDRadio, NDText]:
                if isinstance(data['answer'], dict):
                    matched = NDRadio
                elif isinstance(data['answer'], str):
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
        results = {'definitions': {}}
        for cl in cls.get_union_types():
            schema = cl.schema()
            results['definitions'].update(schema.pop('definitions'))
            results[cl.__name__] = schema
        return results


class DataRow(BaseModel):
    id: str


class NDFeatureSchema(BaseModel):
    schemaId: str = LabelboxID


class NDBase(NDFeatureSchema):
    ontology_type: str
    uuid: UUID
    dataRow: DataRow

    def validate_datarow(self, valid_datarows):
        if self.dataRow.id not in valid_datarows:
            raise ValueError(
                f"datarow {self.dataRow.id} is not attached to the specified project"
            )

    def validate_feature_schemas(self, valid_feature_schemas):
        if self.schemaId not in valid_feature_schemas:
            raise ValueError(
                f"schema id {self.schemaId} is not valid for the provided project's ontology."
            )

        if self.ontology_type != valid_feature_schemas[self.schemaId]['tool']:
            raise ValueError(
                f"Schema id {self.schemaId} does not map to the assigned tool {valid_feature_schemas[self.schemaId]['tool']}"
            )

    def validate_instance(self, valid_datarows, valid_feature_schemas):
        self.validate_feature_schemas(valid_feature_schemas)
        self.validate_datarow(valid_datarows)

    class Config:
        #Users shouldn't to add extra data to the payload
        extra = 'forbid'

        @staticmethod
        def determinants(parent_cls) -> List[str]:
            #This is a hack for better error messages
            return [
                k for k, v in parent_cls.__fields__.items()
                if 'determinant' in v.field_info.extra
            ]


###### Classifications ######


class NDText(NDBase):
    ontology_type: Literal["text"] = "text"
    answer: str = pydantic.Field(determinant=True)
    #No feature schema to check


class NDChecklist(VideoSupported, NDBase):
    ontology_type: Literal["checklist"] = "checklist"
    answers: List[NDFeatureSchema] = pydantic.Field(determinant=True)

    @validator('answers', pre=True)
    def validate_answers(cls, value, field):
        #constr not working with mypy.
        if not len(value):
            raise ValueError("Checklist answers should not be empty")
        return value

    def validate_feature_schemas(self, valid_feature_schemas):
        #Test top level feature schema for this tool
        super(NDChecklist, self).validate_feature_schemas(valid_feature_schemas)
        #Test the feature schemas provided to the answer field
        if len(set([answer.schemaId for answer in self.answers])) != len(
                self.answers):
            raise ValueError(
                f"Duplicated featureSchema found for checklist {self.uuid}")
        for answer in self.answers:
            options = valid_feature_schemas[self.schemaId]['options']
            if answer.schemaId not in options:
                raise ValueError(
                    f"Feature schema provided to {self.ontology_type} invalid. Expected on of {options}. Found {answer}"
                )


class NDRadio(VideoSupported, NDBase):
    ontology_type: Literal["radio"] = "radio"
    answer: NDFeatureSchema = pydantic.Field(determinant=True)

    def validate_feature_schemas(self, valid_feature_schemas):
        super(NDRadio, self).validate_feature_schemas(valid_feature_schemas)
        options = valid_feature_schemas[self.schemaId]['options']
        if self.answer.schemaId not in options:
            raise ValueError(
                f"Feature schema provided to {self.ontology_type} invalid. Expected on of {options}. Found {self.answer.schemaId}"
            )


#A union with custom construction logic to improve error messages
class NDClassification(
        SpecialUnion,
        Type[Union[NDText, NDRadio,  # type: ignore
                   NDChecklist]]):
    ...


###### Tools ######


class NDBaseTool(NDBase):
    classifications: List[NDClassification] = []

    #This is indepdent of our problem
    def validate_feature_schemas(self, valid_feature_schemas):
        for classification in self.classifications:
            classification.validate_feature_schemas(
                valid_feature_schemas[self.schemaId]['classifications'])

    @validator('classifications', pre=True)
    def validate_subclasses(cls, value, field):
        #Create uuid and datarow id so we don't have to define classification objects twice
        #This is caused by the fact that we require these ids for top level classifications but not for subclasses
        results = []
        dummy_id = 'child'.center(25, '_')
        for row in value:
            results.append({
                **row, 'dataRow': {
                    'id': dummy_id
                },
                'uuid': str(uuid4())
            })
        return results


class NDPolygon(NDBaseTool):
    ontology_type: Literal["polygon"] = "polygon"
    polygon: List[Point] = pydantic.Field(determinant=True)

    @validator('polygon')
    def is_geom_valid(cls, v):
        if len(v) < 3:
            raise ValueError(
                f"A polygon must have at least 3 points to be valid. Found {v}")
        return v


class NDPolyline(NDBaseTool):
    ontology_type: Literal["line"] = "line"
    line: List[Point] = pydantic.Field(determinant=True)

    @validator('line')
    def is_geom_valid(cls, v):
        if len(v) < 2:
            raise ValueError(
                f"A line must have at least 2 points to be valid. Found {v}")
        return v


class NDRectangle(NDBaseTool):
    ontology_type: Literal["rectangle"] = "rectangle"
    bbox: Bbox = pydantic.Field(determinant=True)
    #Could check if points are positive


class NDPoint(NDBaseTool):
    ontology_type: Literal["point"] = "point"
    point: Point = pydantic.Field(determinant=True)
    #Could check if points are positive


class EntityLocation(BaseModel):
    start: int
    end: int


class NDTextEntity(NDBaseTool):
    ontology_type: Literal["named-entity"] = "named-entity"
    location: EntityLocation = pydantic.Field(determinant=True)

    @validator('location')
    def is_valid_location(cls, v):
        if isinstance(v, BaseModel):
            v = v.dict()

        if len(v) < 2:
            raise ValueError(
                f"A line must have at least 2 points to be valid. Found {v}")
        if v['start'] < 0:
            raise ValueError(f"Text location must be positive. Found {v}")
        if v['start'] >= v['end']:
            raise ValueError(
                f"Text start location must be less than end. Found {v}")
        return v


class MaskFeatures(BaseModel):
    instanceURI: str
    colorRGB: Union[List[int], Tuple[int, int, int]]


class NDMask(NDBaseTool):
    ontology_type: Literal["superpixel"] = "superpixel"
    mask: MaskFeatures = pydantic.Field(determinant=True)

    @validator('mask')
    def is_valid_mask(cls, v):
        if isinstance(v, BaseModel):
            v = v.dict()

        colors = v['colorRGB']
        #Does the dtype matter? Can it be a float?
        if not isinstance(colors, (tuple, list)):
            raise ValueError(
                f"Received color that is not a list or tuple. Found : {colors}")
        elif len(colors) != 3:
            raise ValueError(
                f"Must provide RGB values for segmentation colors. Found : {colors}"
            )
        elif not all([0 <= color <= 255 for color in colors]):
            raise ValueError(
                f"All rgb colors must be between 0 and 255. Found : {colors}")
        return v


#A union with custom construction logic to improve error messages
class NDTool(
        SpecialUnion,
        Type[Union[NDMask,  # type: ignore
                   NDTextEntity, NDPoint, NDRectangle, NDPolyline,
                   NDPolygon,]]):
    ...


class NDAnnotation(
        SpecialUnion,
        Type[Union[NDTool,  # type: ignore
                   NDClassification]]):

    @classmethod
    def build(cls: Any, data) -> "NDBase":
        if not isinstance(data, dict):
            raise ValueError('value must be dict')
        errors = []
        for cl in cls.get_union_types():
            try:
                return cl(**data)
            except KeyError as e:
                errors.append(f"{cl.__name__}: {e}")

        raise ValueError('Unable to construct any annotation.\n{}'.format(
            "\n".join(errors)))

    @classmethod
    def schema(cls):
        data = {'definitions': {}}
        for type_ in cls.get_union_types():
            schema_ = type_.schema()
            data['definitions'].update(schema_.pop('definitions'))
            data[type_.__name__] = schema_
        return data
