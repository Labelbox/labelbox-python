import datetime
from enum import Enum
from itertools import groupby, chain
from typing import List, Optional, Dict, Union, Callable

from pydantic import BaseModel, conlist, constr

from labelbox.schema.ontology import SchemaId


class DataRowMetadataKind(Enum):
    datetime = "CustomMetadataDateTime"
    enum = "CustomMetadataEnum"
    string = "CustomMetadataString"
    option = "CustomMetadataEnumOption"
    embedding = "CustomMetadataEmbedding"


# Metadata schema
class DataRowMetadataSchema(BaseModel):
    id: SchemaId
    name: constr(strip_whitespace=True, min_length=1, max_length=100)
    reserved: bool
    kind: DataRowMetadataKind
    options: Optional[List["DataRowMetadataSchema"]]

DataRowMetadataSchema.update_forward_refs()

# Constraints for metadata values
Embedding = conlist(float, min_items=128, max_items=128)
DateTime = datetime.datetime  # must be in UTC
String = constr(max_length=500)
OptionId = SchemaId  # enum option

DataRowMetadataValue = Union[Embedding, DateTime, String, OptionId]


# Metadata base class
class DataRowMetadata(BaseModel):
    schema_id: SchemaId
    value: DataRowMetadataValue


# --- Batch Operations ---
class UpsertDataRowMetadata(BaseModel):
    data_row_id: str
    fields: List[DataRowMetadata]


class DeleteDataRowMetadata(BaseModel):
    data_row_id: str
    fields: List[SchemaId]


class DataRowMetadataBatchResponseFields:
    schema_id: str
    value: DataRowMetadataValue


class DataRowMetadataBatchResponse:
    data_row_id: str
    error: str
    fields: List[DataRowMetadataBatchResponseFields]


# --- Batch GraphQL Objects ---
# Don't want to crowd the name space with internals

# Bulk upsert values
class _UpsertDataRowMetadataInput(BaseModel):
    schemaId: str
    value: Union[str, List, dict]


# Batch of upsert values for a datarow
class _UpsertBatchDataRowMetadata(BaseModel):
    dataRowId: str
    fields: List[_UpsertDataRowMetadataInput]


class _DeleteBatchDataRowMetadata(BaseModel):
    dataRowId: str
    fields: List[SchemaId]


_BatchInputs = Union[List[_UpsertBatchDataRowMetadata], List[_DeleteBatchDataRowMetadata]]
_BatchFunction = Callable[[_BatchInputs], List[DataRowMetadataBatchResponse]]


class DataRowMetadataOntology:

    def __init__(self, client):
        self.client = client

        # TODO: consider making these properties to stay in sync with server
        self._raw_ontology: Dict = self._get_ontology()
        # all fields
        self.all_fields: List[DataRowMetadataSchema] = self._parse_ontology()
        self.all_fields_id_index: Dict[SchemaId, DataRowMetadataSchema] = {f.id: f for f in self.all_fields}
        # reserved fields
        self.reserved_fields: List[DataRowMetadataSchema] = [f for f in self.all_fields if f.reserved]
        self.reserved_name_index: Dict[str, DataRowMetadataSchema] = {f.name: f for f in self.reserved_fields}
        self.reserved_id_index: Dict[SchemaId, DataRowMetadataSchema] = {f.id: f for f in self.reserved_fields}
        # custom fields
        self.custom_fields: List[DataRowMetadataSchema] = [f for f in self.all_fields if not f.reserved]
        self.custom_name_index: Dict[str, DataRowMetadataSchema] = {f.name: f for f in self.custom_fields}
        self.custom_id_index: Dict[SchemaId, DataRowMetadataSchema] = {f.id: f for f in self.custom_fields}

    def _get_ontology(self):
        query = """query GetMetadataOntologyBetaPyApi {
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
                    options.append(DataRowMetadataSchema(**option))

            schema["options"] = options
            fields.append(DataRowMetadataSchema(**schema))

        return fields

    def bulk_upsert(self, metadata: List[UpsertDataRowMetadata]) -> List[DataRowMetadataBatchResponse]:
        """Upsert datarow metadata

        Args:
            metadata: DataRow Metadata

        Returns:
            response: []
        """

        if not (len(metadata)):
            raise ValueError("Empty list passed")

        def _batch_upsert(upserts: List[_UpsertBatchDataRowMetadata]) -> List[DataRowMetadataBatchResponse]:

            query = """mutation UpsertDataRowMetadataBetaPyApi($metadata: [DataRowCustomMetadataBatchUpsertInput!]!) {
            upsertDataRowCustomMetadata(data: $metadata){
                dataRowId
                error
                fields {
                    value
                    schemaId
                }
            }
            }"""

            return self.client.execute(query, {"metadata": upserts})

        items = []
        # use group by to minimize unnecessary ops
        for k, g in groupby(metadata, key=lambda x: x.data_row_id):
            items.append(
                _UpsertBatchDataRowMetadata(
                    dataRowId=k,
                    fields=list(chain.from_iterable(self._parse_metadata_upsert(m) for m in g)))

            )

        return _batch_operations(_batch_upsert, items)

    def bulk_delete(self, deletes: List[DeleteDataRowMetadata]) -> List[DataRowMetadataBatchResponse]:

        if not len(deletes):
            raise ValueError("empty array passed")

        def _batch_delete(deletes: List[_DeleteBatchDataRowMetadata]) -> List[DataRowMetadataBatchResponse]:
            query = """mutation DeleteDataRowMetadataBetaPyApi($deletes: [DataRowCustomMetadataBatchDeleteInput!]!) {
              deleteDataRowCustomMetadata(data: $deletes) {
                dataRowId
                error
                fields {
                  value
                  schemaId
                }
              }
            }
            """
            return self.client.execute(query, {"deletes": deletes})

        items = []
        # use group by to minimize unnecessary ops
        for k, g in groupby(deletes, key=lambda x: x.data_row_id):
            items.append(
                _DeleteBatchDataRowMetadata(
                    dataRowId=k,
                    fields=list(g)
                )
            )

        return _batch_operations(_batch_delete, items)

    def _parse_metadata_upsert(
            self,
            metadatum: DataRowMetadata
    ) -> List[_UpsertDataRowMetadataInput]:
        """Format for metadata upserts to GQL"""

        if metadatum.schema_id not in self.all_fields_id_index:
            raise ValueError(f"Schema Id `{metadatum.schema_id}` not found")
        schema = self.all_fields_id_index[metadatum.schema_id]

        if schema["kind"] == DataRowMetadataKind.datetime:
            parsed = _validate_parse_datetime(metadatum)
        elif schema["kind"] == DataRowMetadataKind.string:
            parsed = _validate_parse_text(metadatum)
        elif schema["kind"] == DataRowMetadataKind.enum:
            parsed = _validate_enum_parse(schema, metadatum)
        elif schema["kind"] == DataRowMetadataKind.embedding:
            parsed = _validate_parse_embedding(metadatum)
        elif schema["kind"] == DataRowMetadataKind.option:
            raise ValueError("The option id should ")
        else:
            raise ValueError(f"Unknown type: {schema}")

        return [_UpsertDataRowMetadataInput(**p) for p in parsed]


def _batch_items(iterable, size):
    l = len(iterable)
    for ndx in range(0, l, size):
        yield iterable[ndx:min(ndx + size, l)]


def _batch_operations(
        batch_function: _BatchFunction,
        items: List,
        batch_size: int = 500,
):
    response = []
    for batch in _batch_items(items, batch_size):
        response += batch_function(batch)
        if len(response):
            raise ValueError(response)

    return response


def _validate_parse_embedding(field: DataRowMetadata):
    return [
        {
            "schemaId": field.schema_id,
            "value": field.value,
        }
    ]


def _validate_parse_datetime(field: DataRowMetadata):
    # TODO: better validate tzinfo
    return [
        {
            "schemaId": field.schema_id,
            "value": field.value.isoformat() + "Z",  # needs to be UTC
        }
    ]


def _validate_parse_text(field: DataRowMetadata):
    if not isinstance(field.value, str):
        raise ValueError("Invalid value")

    return [
        {
            "schemaId": field.schema_id,
            "value": field.value,
        }
    ]


def _validate_enum_parse(schema: DataRowMetadataSchema, field: DataRowMetadata):
    if field.value not in {o.id for o in schema.options}:
        raise ValueError(f"Option `{field.value}` not found for {field.schema_id}")

    return [
        {"schemaId": field.schema_id, "value": {}},
        {"schemaId": field.value, "value": {}}
    ]
