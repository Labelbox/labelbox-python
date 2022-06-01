# type: ignore
from datetime import datetime
import warnings
from copy import deepcopy
from enum import Enum
from itertools import chain
from typing import List, Optional, Dict, Union, Callable, Type, Any, Generator

from pydantic import BaseModel, conlist, constr

from labelbox.schema.ontology import SchemaId
from labelbox.utils import camel_case


class DataRowMetadataKind(Enum):
    number = "CustomMetadataNumber"
    datetime = "CustomMetadataDateTime"
    enum = "CustomMetadataEnum"
    string = "CustomMetadataString"
    option = "CustomMetadataEnumOption"
    embedding = "CustomMetadataEmbedding"


# Metadata schema
class DataRowMetadataSchema(BaseModel):
    uid: SchemaId
    name: constr(strip_whitespace=True, min_length=1, max_length=100)
    reserved: bool
    kind: DataRowMetadataKind
    options: Optional[List["DataRowMetadataSchema"]]
    parent: Optional[SchemaId]


DataRowMetadataSchema.update_forward_refs()

Embedding: Type[List[float]] = conlist(float, min_items=128, max_items=128)
String: Type[str] = constr(max_length=500)


class _CamelCaseMixin(BaseModel):

    class Config:
        allow_population_by_field_name = True
        alias_generator = camel_case


# Metadata base class
class DataRowMetadataField(_CamelCaseMixin):
    schema_id: SchemaId
    # value is of type `Any` so that we do not improperly coerce the value to the wrong tpye
    # Additional validation is performed before upload using the schema information
    value: Any


class DataRowMetadata(_CamelCaseMixin):
    data_row_id: str
    fields: List[DataRowMetadataField]


class DeleteDataRowMetadata(_CamelCaseMixin):
    data_row_id: str
    fields: List[SchemaId]


class DataRowMetadataBatchResponse(_CamelCaseMixin):
    data_row_id: str
    error: Optional[str] = None
    fields: List[Union[DataRowMetadataField, SchemaId]]


# --- Batch GraphQL Objects ---
# Don't want to crowd the name space with internals


# Bulk upsert values
class _UpsertDataRowMetadataInput(_CamelCaseMixin):
    schema_id: str
    value: Any


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

        self._client = client
        self._batch_size = 50  # used for uploads and deletes

        self._raw_ontology = self._get_ontology()
        self._build_ontology()

    def _build_ontology(self):
        # all fields
        self.fields = self._parse_ontology(self._raw_ontology)
        self.fields_by_id = self._make_id_index(self.fields)

        # reserved fields
        self.reserved_fields: List[DataRowMetadataSchema] = [
            f for f in self.fields if f.reserved
        ]
        self.reserved_by_id = self._make_id_index(self.reserved_fields)
        self.reserved_by_name: Dict[
            str,
            DataRowMetadataSchema] = self._make_name_index(self.reserved_fields)

        # custom fields
        self.custom_fields: List[DataRowMetadataSchema] = [
            f for f in self.fields if not f.reserved
        ]
        self.custom_by_id = self._make_id_index(self.custom_fields)
        self.custom_by_name: Dict[
            str,
            DataRowMetadataSchema] = self._make_name_index(self.custom_fields)

    @staticmethod
    def _make_name_index(fields: List[DataRowMetadataSchema]):
        index = {}
        for f in fields:
            if f.options:
                index[f.name] = {}
                for o in f.options:
                    index[f.name][o.name] = o
            else:
                index[f.name] = f
        return index

    @staticmethod
    def _make_id_index(
        fields: List[DataRowMetadataSchema]
    ) -> Dict[SchemaId, DataRowMetadataSchema]:
        index = {}
        for f in fields:
            index[f.uid] = f
            if f.options:
                for o in f.options:
                    index[o.uid] = o
        return index

    def _get_ontology(self) -> List[Dict[str, Any]]:
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
        return self._client.execute(query)["customMetadataOntology"]

    @staticmethod
    def _parse_ontology(raw_ontology) -> List[DataRowMetadataSchema]:
        fields = []
        copy = deepcopy(raw_ontology)
        for schema in copy:
            schema["uid"] = schema["id"]
            options = None
            if schema.get("options"):
                options = []
                for option in schema["options"]:
                    option["uid"] = option["id"]
                    options.append(
                        DataRowMetadataSchema(**{
                            **option,
                            **{
                                "parent": schema["uid"]
                            }
                        }))
            schema["options"] = options
            fields.append(DataRowMetadataSchema(**schema))

        return fields

    def refresh_ontology(self):
        self._raw_ontology = self._get_ontology()
        self._build_ontology()

    def parse_metadata(
        self, unparsed: List[Dict[str,
                                  List[Union[str,
                                             Dict]]]]) -> List[DataRowMetadata]:
        """ Parse metadata responses

        >>> mdo.parse_metadata([metadata])

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
                if f["schemaId"] not in self.fields_by_id:
                    # Update metadata ontology if field can't be found
                    self.refresh_ontology()
                    if f["schemaId"] not in self.fields_by_id:
                        raise ValueError(
                            f"Schema Id `{f['schemaId']}` not found in ontology"
                        )

                schema = self.fields_by_id[f["schemaId"]]
                if schema.kind == DataRowMetadataKind.enum:
                    continue
                elif schema.kind == DataRowMetadataKind.option:
                    field = DataRowMetadataField(schema_id=schema.parent,
                                                 value=schema.uid)
                elif schema.kind == DataRowMetadataKind.datetime:
                    field = DataRowMetadataField(
                        schema_id=schema.uid,
                        value=datetime.fromisoformat(f["value"][:-1] +
                                                     "+00:00"))
                else:
                    field = DataRowMetadataField(schema_id=schema.uid,
                                                 value=f["value"])
                fields.append(field)
            parsed.append(
                DataRowMetadata(data_row_id=dr["dataRowId"], fields=fields))
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
            res = self._client.execute(
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
            res = self._client.execute(
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

    def bulk_export(self, data_row_ids: List[str]) -> List[DataRowMetadata]:
        """ Exports metadata for a list of data rows

        >>> mdo.bulk_export([data_row.uid for data_row in data_rows])

        Args:
            data_row_ids: List of data data rows to fetch metadata for
        Returns:
            A list of DataRowMetadata.
            There will be one DataRowMetadata for each data_row_id passed in.
            This is true even if the data row does not have any meta data.
            Data rows without metadata will have empty `fields`.

        """

        if not len(data_row_ids):
            raise ValueError("Empty list passed")

        def _bulk_export(_data_row_ids: List[str]) -> List[DataRowMetadata]:
            query = """query dataRowCustomMetadataPyApi($dataRowIds: [ID!]!) {
                dataRowCustomMetadata(where: {dataRowIds : $dataRowIds}) {
                    dataRowId
                    fields {
                        value
                        schemaId
                    }
                }
            }
            """
            return self.parse_metadata(
                self._client.execute(
                    query,
                    {"dataRowIds": _data_row_ids})['dataRowCustomMetadata'])

        return _batch_operations(_bulk_export,
                                 data_row_ids,
                                 batch_size=self._batch_size)

    def _parse_upsert(
            self, metadatum: DataRowMetadataField
    ) -> List[_UpsertDataRowMetadataInput]:
        """Format for metadata upserts to GQL"""

        if metadatum.schema_id not in self.fields_by_id:
            # Update metadata ontology if field can't be found
            self.refresh_ontology()
            if metadatum.schema_id not in self.fields_by_id:
                raise ValueError(
                    f"Schema Id `{metadatum.schema_id}` not found in ontology")

        schema = self.fields_by_id[metadatum.schema_id]

        if schema.kind == DataRowMetadataKind.datetime:
            parsed = _validate_parse_datetime(metadatum)
        elif schema.kind == DataRowMetadataKind.string:
            parsed = _validate_parse_text(metadatum)
        elif schema.kind == DataRowMetadataKind.number:
            parsed = _validate_parse_number(metadatum)
        elif schema.kind == DataRowMetadataKind.embedding:
            parsed = _validate_parse_embedding(metadatum)
        elif schema.kind == DataRowMetadataKind.enum:
            parsed = _validate_enum_parse(schema, metadatum)
        elif schema.kind == DataRowMetadataKind.option:
            raise ValueError("An Option id should not be set as the Schema id")
        else:
            raise ValueError(f"Unknown type: {schema}")

        return [_UpsertDataRowMetadataInput(**p) for p in parsed]

    # Convert metadata to DataRowMetadataField objects, parse all fields
    # and return a dictionary of metadata fields for upsert
    def parse_upsert_metadata(self, metadata_fields):

        def _convert_metadata_field(metadata_field):
            if isinstance(metadata_field, DataRowMetadataField):
                return metadata_field
            elif isinstance(metadata_field, dict):
                if not all(key in metadata_field
                           for key in ("schema_id", "value")):
                    raise ValueError(
                        f"Custom metadata field '{metadata_field}' must have 'schema_id' and 'value' keys"
                    )
                return DataRowMetadataField(
                    schema_id=metadata_field["schema_id"],
                    value=metadata_field["value"])
            else:
                raise ValueError(
                    f"Metadata field '{metadata_field}' is neither 'DataRowMetadataField' type or a dictionary"
                )

        # Convert all metadata fields to DataRowMetadataField type
        metadata_fields = [_convert_metadata_field(m) for m in metadata_fields]
        parsed_metadata = list(
            chain.from_iterable(self._parse_upsert(m) for m in metadata_fields))
        return [m.dict(by_alias=True) for m in parsed_metadata]

    def _validate_delete(self, delete: DeleteDataRowMetadata):
        if not len(delete.fields):
            raise ValueError(f"No fields specified for {delete.data_row_id}")

        deletes = set()
        for schema_id in delete.fields:
            if schema_id not in self.fields_by_id:
                # Update metadata ontology if field can't be found
                self.refresh_ontology()
                if schema_id not in self.fields_by_id:
                    raise ValueError(
                        f"Schema Id `{schema_id}` not found in ontology")

            schema = self.fields_by_id[schema_id]
            # handle users specifying enums by adding all option enums
            if schema.kind == DataRowMetadataKind.enum:
                [deletes.add(o.uid) for o in schema.options]

            deletes.add(schema.uid)

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

    if isinstance(field.value, list):
        if not (Embedding.min_items <= len(field.value) <= Embedding.max_items):
            raise ValueError(
                "Embedding length invalid. "
                "Must have length within the interval "
                f"[{Embedding.min_items},{Embedding.max_items}]. Found {len(field.value)}"
            )
        field.value = [float(x) for x in field.value]
    else:
        raise ValueError(
            f"Expected a list for embedding. Found {type(field.value)}")
    return [field.dict(by_alias=True)]


def _validate_parse_number(
    field: DataRowMetadataField
) -> List[Dict[str, Union[SchemaId, str, float, int]]]:
    field.value = float(field.value)
    return [field.dict(by_alias=True)]


def _validate_parse_datetime(
        field: DataRowMetadataField) -> List[Dict[str, Union[SchemaId, str]]]:
    if isinstance(field.value, str):
        if field.value.endswith("Z"):
            field.value = field.value[:-1]
        field.value = datetime.fromisoformat(field.value)
    elif not isinstance(field.value, datetime):
        raise TypeError(
            f"value for datetime fields must be either a string or datetime object. Found {type(field.value)}"
        )

    return [{
        "schemaId": field.schema_id,
        "value": field.value.isoformat() + "Z",  # needs to be UTC
    }]


def _validate_parse_text(
        field: DataRowMetadataField) -> List[Dict[str, Union[SchemaId, str]]]:
    if not isinstance(field.value, str):
        raise ValueError(
            f"Expected a string type for the text field. Found {type(field.value)}"
        )

    if len(field.value) > String.max_length:
        raise ValueError(
            f"string fields cannot exceed {String.max_length} characters.")

    return [field.dict(by_alias=True)]


def _validate_enum_parse(
        schema: DataRowMetadataSchema,
        field: DataRowMetadataField) -> List[Dict[str, Union[SchemaId, dict]]]:
    if schema.options:
        if field.value not in {o.uid for o in schema.options}:
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
