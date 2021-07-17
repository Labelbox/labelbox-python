import datetime
from enum import Enum
from typing import List, Optional, Dict, Union

from pydantic import BaseModel, conlist

from labelbox.orm.db_object import DbObject
from labelbox.schema.ontology import SchemaId


class DataRowMetadataKind(Enum):
    datetime = "DataRowMetadataDateTime"
    enum = "DataRowMetadataEnum"
    text = "DataRowMetadataString"
    option = "DataRowMetadataEnumOption"
    embedding = "DataRowMetadataEmbedding"


class DataRowMetadataSchema(BaseModel):
    id: SchemaId
    name: str
    reserved: bool
    kind: DataRowMetadataKind
    options: Optional[List["DataRowMetadataSchema"]]


class DataRowMetadata(BaseModel):
    schema_id: SchemaId
    value: str


class DataRowMetadataText(DataRowMetadata):
    value: str


class DataRowMetadataDateTime(DataRowMetadata):
    value: datetime.datetime


class DataRowMetadataEmbedding(DataRowMetadata):
    value: conlist(float, min_items=128, max_items=128)


class DataRowMetadataEnum(DataRowMetadata):
    option_id: str


DataRowMetadata = Union[DataRowMetadataText, DataRowMetadataDateTime, DataRowMetadataEnum, DataRowMetadataEmbedding]


class UpsertDataRowMetadata(BaseModel):
    data_row_id: str
    metadata: List[DataRowMetadata]

class DeleteDataRowMetadata(BaseModel):
    data_row_id: str
    schema_ids: List[SchemaId]

class DataRowMetadataOntology(DbObject):

    def __init__(self, client):
        super().__init__(client, {})

        # TODO: consider making these methods to stay in sync with server
        self._raw_ontology = self._get_ontology()
        self.fields: List[DataRowMetadataSchema] = self._parse_ontology()
        self.reserved_fields: List[DataRowMetadataSchema] = [f for f in self.fields if f.reserved]
        self.custom_fields: List[DataRowMetadataSchema] = [f for f in self.fields if not f.reserved]
        self.reserved_name_index: Dict[str, DataRowMetadataSchema] = {f.name: f for f in self.reserved_fields}
        self.reserved_id_index: Dict[SchemaId, DataRowMetadataSchema] = {f.id: f for f in self.reserved_fields}
        self.custom_name_index: Dict[str, DataRowMetadataSchema] = {f.name: f for f in self.custom_fields}
        self.custom_id_index: Dict[SchemaId, DataRowMetadataSchema] = {f.id: f for f in self.custom_fields}

    def _get_ontology(self):
        query = """query GetMetadataOntologyPyBeta {
        customMetadataOntology {
                id
                name
                kind
                reserved
                options {
                  id
                  kind
                  name
                  reserved
                }
              }
            }
        """
        return self.client.execute(query)["customMetadataOntology"]

    def _parse_ontology(self):

        fields = []
        for schema in self._raw_ontology:
            options = None
            if schema.get("options"):
                options = []
                for option in schema["options"]:
                    option["kind"] = DataRowMetadataKind.option
                    option["parent"] = {
                        "id": schema["id"],
                        "name": schema["name"]
                    }
                    option["id"] = option
                    options.append(DataRowMetadataSchema(**option))

            schema["options"] = options
            fields.append(DataRowMetadataSchema(**schema))

        return fields

    def bulk_upsert(self, metadata: List[UpsertDataRowMetadata]):
        """

        Args:
            metadata:

        Returns:

        """
        query = """mutation UpsertDataRowMetadataPyBeta($datarowMetadata: DataRowCustomMetadataBatchUpsertInput!) {
            upsertDataRowCustomMetadata(data: [$datarowMetadata]){
                dataRowId
                error
                fields {
                    value
                    schemaId
                }
            }
        }"""

        self.client.execute(query)

    def bulk_delete(self, metadata: List[DeleteDataRowMetadata]):
        pass


def _validate_metadata(ontology, field):
    schema = ontology.lookup_id(field.schemaId)

    if schema["kind"] == DataRowMetadataKind.datetime:
        return _validate_datetime(field)
    elif schema["kind"] == DataRowMetadataKind.text:
        return _validate_text(field)
    elif schema["kind"] == DataRowMetadataKind.enum:
        return _validate_enum(field)
    elif schema["kind"] == DataRowMetadataKind.option:
        raise ValueError("SchemaId should be for the enum not the option")
    elif schema["kind"] == DataRowMetadataKind.embedding:
        return _valdiate_embedding(field)
    else:
        raise ValueError


def _valdiate_embedding(field):
    if len(field.value) != 128:
        raise ValueError("Vector must be of length 128")

    array = field.value

    return [
        {
            "schemaId": field.schemaId,
            "value": array,
        }
    ]


def _validate_datetime(field):
    if not isinstance(field.value, datetime.datetime):
        raise ValueError("Not python datetimes")

    # TODO: validate tzinfo
    return [
        {
            "schemaId": field.schemaId,
            "value": field.value.isoformat() + "Z",  # needs to be UTC
        }
    ]


def _validate_text(field):
    if not isinstance(field.value, str):
        raise ValueError("Invalid value")

    return [{
        "schemaId": field.schemaId,
        "value": field.value,
    }]


def _validate_enum(field):
    return [
        {"schemaId": field.schemaId, "value": {}},
        {"schemaId": field.optionId, "value": {}}
    ]
