import datetime
from enum import Enum
from itertools import chain
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
class DataRowMetadataField(BaseModel):
    schema_id: SchemaId
    value: DataRowMetadataValue


class DataRowMetadata(BaseModel):
    data_row_id: str
    fields: List[DataRowMetadataField]


# --- Batch Operations ---
class UpsertDataRowMetadata(BaseModel):
    data_row_id: str
    fields: List[DataRowMetadataField]


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
    schemaIds: List[SchemaId]


_BatchInputs = Union[List[_UpsertBatchDataRowMetadata], List[_DeleteBatchDataRowMetadata]]
_BatchFunction = Callable[[_BatchInputs], List[DataRowMetadataBatchResponse]]


class DataRowMetadataOntology:
    """ Ontology for data row metadata

    Metadata provides additional context for a data rows. Metadata is broken into two classes
    reserved and custom. Reserved fields are defined by Labelbox and used for creating
    specific experiences in the platform.

    """

    def __init__(self, client):
        self.client = client

        # TODO: consider making these properties to stay in sync with server
        self._raw_ontology: Dict = self._get_ontology()
        # all fields
        self.all_fields: List[DataRowMetadataSchema] = self._parse_ontology()
        self.all_fields_id_index: Dict[SchemaId, DataRowMetadataSchema] = self._make_id_index(self.all_fields)
        # reserved fields
        self.reserved_fields: List[DataRowMetadataSchema] = [f for f in self.all_fields if f.reserved]
        self.reserved_id_index: Dict[SchemaId, DataRowMetadataSchema] = self._make_id_index(self.reserved_fields)
        self.reserved_name_index: Dict[str, DataRowMetadataSchema] = {f.name: f for f in self.reserved_fields}
        # custom fields
        self.custom_fields: List[DataRowMetadataSchema] = [f for f in self.all_fields if not f.reserved]
        self.custom_id_index: Dict[SchemaId, DataRowMetadataSchema] = self._make_id_index(self.custom_fields)
        self.custom_name_index: Dict[str, DataRowMetadataSchema] = {f.name: f for f in self.custom_fields}

    @staticmethod
    def _make_id_index(fields: List[DataRowMetadataSchema]) -> Dict[SchemaId, DataRowMetadataSchema]:
        index = {}
        for f in fields:
            index[f.id] = f
            if f.options:
                for o in f.options:
                    index[o.id] = f.id
        return index

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
                options = [DataRowMetadataSchema(**option) for option in schema["options"]]

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
        # TODO: use groupby to minimize unnecessary ops
        # for k, g in groupby(
        #         sorted(metadata, key=lambda x: x.data_row_id),
        #         key=lambda x: x.data_row_id
        # ):

        #
        for m in metadata:
            items.append(
                _UpsertBatchDataRowMetadata(
                    dataRowId=m.data_row_id,
                    fields=list(
                        chain.from_iterable(self._parse_upsert(m) for m in m.fields))
                ).dict()
            )

        return _batch_operations(_batch_upsert, items)

    def bulk_delete(self, deletes: List[DeleteDataRowMetadata]) -> List[DataRowMetadataBatchResponse]:

        if not len(deletes):
            raise ValueError("Empty list passed")

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
        for m in deletes:
            items.append(self._validate_delete(m))

        return _batch_operations(_batch_delete, items)

    def _parse_upsert(
            self,
            metadatum: DataRowMetadataField
    ) -> List[_UpsertDataRowMetadataInput]:
        """Format for metadata upserts to GQL"""

        if metadatum.schema_id not in self.all_fields_id_index:
            raise ValueError(f"Schema Id `{metadatum.schema_id}` not found in ontology")

        schema = self.all_fields_id_index[metadatum.schema_id]

        if schema.kind == DataRowMetadataKind.datetime:
            parsed = _validate_parse_datetime(metadatum)
        elif schema.kind == DataRowMetadataKind.string:
            parsed = _validate_parse_text(metadatum)
        elif schema.kind == DataRowMetadataKind.enum:
            parsed = _validate_enum_parse(schema, metadatum)
        elif schema.kind == DataRowMetadataKind.embedding:
            parsed = _validate_parse_embedding(metadatum)
        elif schema.kind == DataRowMetadataKind.option:
            raise ValueError("An option id should not be as a schema id")
        else:
            raise ValueError(f"Unknown type: {schema}")

        return [_UpsertDataRowMetadataInput(**p) for p in parsed]

    def _validate_delete(self, delete: DeleteDataRowMetadata):

        if not len(delete.fields):
            raise ValueError(f"No fields specified for {delete.data_row_id}")

        for schema_id in delete.fields:
            if schema_id not in self.all_fields_id_index:
                raise ValueError(f"Schema Id `{schema_id}` not found in ontology")

            schema = self.all_fields_id_index[schema_id]
            # TODO: change server implementation to delete by parent only
            # if schema.kind == DataRowMetadataKind.option:
            #     raise ValueError("Specify the parent to remove an option")

        return _DeleteBatchDataRowMetadata(
            dataRowId=delete.data_row_id,
            schemaIds=delete.fields
        ).dict()


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
        # TODO: understand this better
        # if len(response):
        #     raise ValueError(response)

    return response


def _validate_parse_embedding(field: DataRowMetadataField):
    return [
        {
            "schemaId": field.schema_id,
            "value": field.value,
        }
    ]


def _validate_parse_datetime(field: DataRowMetadataField):
    # TODO: better validate tzinfo
    return [
        {
            "schemaId": field.schema_id,
            "value": field.value.isoformat() + "Z",  # needs to be UTC
        }
    ]


def _validate_parse_text(field: DataRowMetadataField):
    if not isinstance(field.value, str):
        raise ValueError("Invalid value")

    return [
        {
            "schemaId": field.schema_id,
            "value": field.value,
        }
    ]


def _validate_enum_parse(schema: DataRowMetadataSchema, field: DataRowMetadataField):
    if field.value not in {o.id for o in schema.options}:
        raise ValueError(f"Option `{field.value}` not found for {field.schema_id}")

    return [
        {"schemaId": field.schema_id, "value": {}},
        {"schemaId": field.value, "value": {}}
    ]
