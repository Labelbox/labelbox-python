# type: ignore
import datetime
from enum import Enum
from itertools import chain
from typing import List, Optional, Dict, Union, Callable, Type, Any, Generator

from pydantic import BaseModel, conlist, constr

from labelbox.schema.ontology import SchemaId
from labelbox.utils import camel_case


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
    parent: Optional[SchemaId]


DataRowMetadataSchema.update_forward_refs()

# Constraints for metadata values
Embedding: Type[List[float]] = conlist(float, min_items=128, max_items=128)
DateTime: Type[datetime.datetime] = datetime.datetime  # must be in UTC
String: Type[str] = constr(max_length=500)
OptionId: Type[SchemaId] = SchemaId  # enum option

DataRowMetadataValue = Union[Embedding, DateTime, String, OptionId]


class _CamelCaseMixin(BaseModel):

    class Config:
        allow_population_by_field_name = True
        alias_generator = camel_case


# Metadata base class
class DataRowMetadataField(_CamelCaseMixin):
    schema_id: SchemaId
    value: DataRowMetadataValue


class DataRowMetadata(_CamelCaseMixin):
    data_row_id: str
    fields: List[DataRowMetadataField]


class DeleteDataRowMetadata(_CamelCaseMixin):
    data_row_id: str
    fields: List[SchemaId]


class DataRowMetadataBatchResponse(_CamelCaseMixin):
    data_row_id: str
    error: str
    fields: List[Union[DataRowMetadataField, SchemaId]]


# --- Batch GraphQL Objects ---
# Don't want to crowd the name space with internals


# Bulk upsert values
class _UpsertDataRowMetadataInput(_CamelCaseMixin):
    schema_id: str
    value: Union[str, List, dict]


# Batch of upsert values for a datarow
class _UpsertBatchDataRowMetadata(_CamelCaseMixin):
    data_row_id: str
    fields: List[_UpsertDataRowMetadataInput]


class _DeleteBatchDataRowMetadata(_CamelCaseMixin):
    data_row_id: str
    schema_ids: List[SchemaId]


_BatchInputs = Union[List[_UpsertBatchDataRowMetadata],
                     List[_DeleteBatchDataRowMetadata]]
_BatchFunction = Callable[[_BatchInputs], List[DataRowMetadataBatchResponse]]


class DataRowMetadataOntology:
    """ Ontology for data row metadata

    Metadata provides additional context for a data rows. Metadata is broken into two classes
    reserved and custom. Reserved fields are defined by Labelbox and used for creating
    specific experiences in the platform.

    >>> mdo = client.get_data_row_metadata_ontology()

    """

    def __init__(self, client):
        self.client = client
        self._batch_size = 50

        # TODO: consider making these properties to stay in sync with server
        self._raw_ontology = self._get_ontology()
        # all fields
        self.all_fields = self._parse_ontology()
        self.all_fields_id_index = self._make_id_index(self.all_fields)
        # reserved fields
        self.reserved_fields: List[DataRowMetadataSchema] = [
            f for f in self.all_fields if f.reserved
        ]
        self.reserved_id_index = self._make_id_index(self.reserved_fields)
        self.reserved_name_index: Dict[str, DataRowMetadataSchema] = {
            f.name: f for f in self.reserved_fields
        }
        # custom fields
        self.custom_fields: List[DataRowMetadataSchema] = [
            f for f in self.all_fields if not f.reserved
        ]
        self.custom_id_index = self._make_id_index(self.custom_fields)
        self.custom_name_index: Dict[str, DataRowMetadataSchema] = {
            f.name: f for f in self.custom_fields
        }

    @staticmethod
    def _make_id_index(
        fields: List[DataRowMetadataSchema]
    ) -> Dict[SchemaId, DataRowMetadataSchema]:
        index = {}
        for f in fields:
            index[f.id] = f
            if f.options:
                for o in f.options:
                    index[o.id] = o
        return index

    def _get_ontology(self) -> Dict[str, Any]:
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
        }}
        """
        return self.client.execute(query)["customMetadataOntology"]

    def _parse_ontology(self) -> List[DataRowMetadataSchema]:
        fields = []
        for schema in self._raw_ontology:
            options = None
            if schema.get("options"):
                options = [
                    DataRowMetadataSchema(**{
                        **option,
                        **{
                            "parent": schema["id"]
                        }
                    }) for option in schema["options"]
                ]
            schema["options"] = options
            fields.append(DataRowMetadataSchema(**schema))

        return fields

    def parse_metadata(
        self, unparsed: List[Dict[str,
                                  List[Union[str,
                                             Dict]]]]) -> List[DataRowMetadata]:
        """ Parse metadata responses

        >>> mdo.parse_metadata([datarow.metadata])

        Args:
            unparsed: An unparsed metadata export

        Returns:
            metadata: List of `DataRowMetadata`

        """
        parsed = []
        if isinstance(unparsed, dict):
            raise ValueError("Pass a list of dictionaries")

        for dr in unparsed:
            fields = []
            for f in dr["fields"]:
                schema = self.all_fields_id_index[f["schema_id"]]
                if schema.kind == DataRowMetadataKind.enum:
                    continue
                elif schema.kind == DataRowMetadataKind.option:
                    field = DataRowMetadataField(schema_id=schema.parent,
                                                 value=schema.id)
                else:
                    field = DataRowMetadataField(schema_id=schema.id,
                                                 value=f["value"])

                fields.append(field)
            parsed.append(
                DataRowMetadata(data_row_id=dr["data_row_id"], fields=fields))
        return parsed

    def bulk_upsert(
            self, metadata: List[DataRowMetadata]
    ) -> List[DataRowMetadataBatchResponse]:
        """Upsert datarow metadata


        >>> metadata = DataRowMetadata(
        >>>                 data_row_id="datarow-id",
        >>>                 fields=[
        >>>                        DataRowMetadataField(schema_id="schema-id", value="my-message"),
        >>>                        ...
        >>>                    ]
        >>>    )
        >>> mdo.batch_upsert([metadata])

        Args:
            metadata: List of DataRow Metadata to upsert

        Returns:
            list of unsuccessful upserts.
            An empty list means the upload was successful.
        """

        if not len(metadata):
            raise ValueError("Empty list passed")

        def _batch_upsert(
            upserts: List[_UpsertBatchDataRowMetadata]
        ) -> List[DataRowMetadataBatchResponse]:
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
            res = self.client.execute(
                query, {"metadata": upserts})['upsertDataRowCustomMetadata']
            return [
                DataRowMetadataBatchResponse(data_row_id=r['dataRowId'],
                                             error=r['error'],
                                             fields=self.parse_metadata(
                                                 [r])[0].fields) for r in res
            ]

        items = []
        for m in metadata:
            items.append(
                _UpsertBatchDataRowMetadata(
                    data_row_id=m.data_row_id,
                    fields=list(
                        chain.from_iterable(
                            self._parse_upsert(m) for m in m.fields))).dict(
                                by_alias=True))

        res = _batch_operations(_batch_upsert, items, self._batch_size)
        return res

    def bulk_delete(
        self, deletes: List[DeleteDataRowMetadata]
    ) -> List[DataRowMetadataBatchResponse]:
        """ Delete metadata from a datarow by specifiying the fields you want to remove

        >>> delete = DeleteDataRowMetadata(
        >>>                 data_row_id="datarow-id",
        >>>                 fields=[
        >>>                        "schema-id-1",
        >>>                        "schema-id-2"
        >>>                        ...
        >>>                    ]
        >>>    )
        >>> mdo.batch_delete([metadata])

        Args:
            deletes: Data row and schema ids to delete

        Returns:
            list of unsuccessful deletions.
            An empty list means all data rows were successfully deleted.

        """

        if not len(deletes):
            raise ValueError("Empty list passed")

        def _batch_delete(
            deletes: List[_DeleteBatchDataRowMetadata]
        ) -> List[DataRowMetadataBatchResponse]:
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
            res = self.client.execute(
                query, {"deletes": deletes})['deleteDataRowCustomMetadata']
            failures = []
            for dr in res:
                dr['fields'] = [f['schemaId'] for f in dr['fields']]
                failures.append(DataRowMetadataBatchResponse(**dr))
            return failures

        items = [self._validate_delete(m) for m in deletes]
        return _batch_operations(_batch_delete,
                                 items,
                                 batch_size=self._batch_size)

    def _parse_upsert(
            self, metadatum: DataRowMetadataField
    ) -> List[_UpsertDataRowMetadataInput]:
        """Format for metadata upserts to GQL"""

        if metadatum.schema_id not in self.all_fields_id_index:
            raise ValueError(
                f"Schema Id `{metadatum.schema_id}` not found in ontology")

        schema = self.all_fields_id_index[metadatum.schema_id]

        if schema.kind == DataRowMetadataKind.datetime:
            parsed = _validate_parse_datetime(metadatum)
        elif schema.kind == DataRowMetadataKind.string:
            parsed = _validate_parse_text(metadatum)
        elif schema.kind == DataRowMetadataKind.embedding:
            parsed = _validate_parse_embedding(metadatum)
        elif schema.kind == DataRowMetadataKind.enum:
            parsed = _validate_enum_parse(schema, metadatum)
        elif schema.kind == DataRowMetadataKind.option:
            raise ValueError("An option id should not be as a schema id")
        else:
            raise ValueError(f"Unknown type: {schema}")

        return [_UpsertDataRowMetadataInput(**p) for p in parsed]

    def _validate_delete(self, delete: DeleteDataRowMetadata):
        if not len(delete.fields):
            raise ValueError(f"No fields specified for {delete.data_row_id}")

        deletes = set()
        for schema_id in delete.fields:
            if schema_id not in self.all_fields_id_index:
                raise ValueError(
                    f"Schema Id `{schema_id}` not found in ontology")

            schema = self.all_fields_id_index[schema_id]
            # handle users specifying enums by adding all option enums
            if schema.kind == DataRowMetadataKind.enum:
                [deletes.add(o.id) for o in schema.options]

            deletes.add(schema.id)

        return _DeleteBatchDataRowMetadata(
            data_row_id=delete.data_row_id,
            schema_ids=list(delete.fields)).dict(by_alias=True)


def _batch_items(iterable: List[Any], size: int) -> Generator[Any, None, None]:
    l = len(iterable)
    for ndx in range(0, l, size):
        yield iterable[ndx:min(ndx + size, l)]


def _batch_operations(
    batch_function: _BatchFunction,
    items: List,
    batch_size: int = 100,
):
    response = []

    for batch in _batch_items(items, batch_size):
        response += batch_function(batch)
    return response


def _validate_parse_embedding(
        field: DataRowMetadataField
) -> List[Dict[str, Union[SchemaId, Embedding]]]:
    return [field.dict(by_alias=True)]


def _validate_parse_datetime(
        field: DataRowMetadataField) -> List[Dict[str, Union[SchemaId, str]]]:
    # TODO: better validate tzinfo
    return [{
        "schemaId": field.schema_id,
        "value": field.value.isoformat() + "Z",  # needs to be UTC
    }]


def _validate_parse_text(
        field: DataRowMetadataField) -> List[Dict[str, Union[SchemaId, str]]]:
    return [field.dict(by_alias=True)]


def _validate_enum_parse(
        schema: DataRowMetadataSchema,
        field: DataRowMetadataField) -> List[Dict[str, Union[SchemaId, dict]]]:
    if schema.options:
        if field.value not in {o.id for o in schema.options}:
            raise ValueError(
                f"Option `{field.value}` not found for {field.schema_id}")
    else:
        raise ValueError("Incorrectly specified enum schema")

    return [{
        "schemaId": field.schema_id,
        "value": {}
    }, {
        "schemaId": field.value,
        "value": {}
    }]
