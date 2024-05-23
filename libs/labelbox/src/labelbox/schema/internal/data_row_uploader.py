import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from typing import Iterable, List, Union

from labelbox.exceptions import InvalidQueryError
from labelbox.exceptions import InvalidAttributeError
from labelbox.exceptions import MalformedQueryException
from labelbox.orm.model import Entity
from labelbox.orm.model import Field
from labelbox.schema.embedding import EmbeddingVector
from labelbox.schema.internal.data_row_create_upsert import DataRowItemBase
from labelbox.schema.internal.datarow_upload_constants import MAX_DATAROW_PER_API_OPERATION


class UploadManifest:

    def __init__(self, source: str, item_count: int, chunk_uris: List[str]):
        self.source = source
        self.item_count = item_count
        self.chunk_uris = chunk_uris

    def to_dict(self):
        return {
            "source": self.source,
            "item_count": self.item_count,
            "chunk_uris": self.chunk_uris
        }


class DataRowUploader:

    @staticmethod
    def create_descriptor_file(client,
                               items,
                               max_attachments_per_data_row=None,
                               is_upsert=False):
        """
        This function is shared by `Dataset.create_data_rows`, `Dataset.create_data_rows_sync` and `Dataset.update_data_rows`.
        It is used to prepare the input file. The user defined input is validated, processed, and json stringified.
        Finally the json data is uploaded to gcs and a uri is returned. This uri can be passed to

        Each element in `items` can be either a `str` or a `dict`. If
        it is a `str`, then it is interpreted as a local file path. The file
        is uploaded to Labelbox and a DataRow referencing it is created.

        If an item is a `dict`, then it could support one of the two following structures
            1. For static imagery, video, and text it should map `DataRow` field names to values.
               At the minimum an `item` passed as a `dict` must contain a `row_data` key and value.
               If the value for row_data is a local file path and the path exists,
               then the local file will be uploaded to labelbox.

            2. For tiled imagery the dict must match the import structure specified in the link below
               https://docs.labelbox.com/data-model/en/index-en#tiled-imagery-import

        >>> dataset.create_data_rows([
        >>>     {DataRow.row_data:"http://my_site.com/photos/img_01.jpg"},
        >>>     {DataRow.row_data:"/path/to/file1.jpg"},
        >>>     "path/to/file2.jpg",
        >>>     {DataRow.row_data: {"tileLayerUrl" : "http://", ...}}
        >>>     {DataRow.row_data: {"type" : ..., 'version' : ..., 'messages' : [...]}}
        >>>     ])

        For an example showing how to upload tiled data_rows see the following notebook:
            https://github.com/Labelbox/labelbox-python/blob/ms/develop/model_assisted_labeling/tiled_imagery_mal.ipynb

        Args:
            items (iterable of (dict or str)): See above for details.
            max_attachments_per_data_row (Optional[int]): Param used during attachment validation to determine
                if the user has provided too many attachments.

        Returns:
            uri (string): A reference to the uploaded json data.

        Raises:
            InvalidQueryError: If the `items` parameter does not conform to
                the specification above or if the server did not accept the
                DataRow creation request (unknown reason).
            InvalidAttributeError: If there are fields in `items` not valid for
                a DataRow.
            ValueError: When the upload parameters are invalid
        """
        file_upload_thread_count = 20
        DataRow = Entity.DataRow
        AssetAttachment = Entity.AssetAttachment

        def upload_if_necessary(item):
            if is_upsert and 'row_data' not in item:
                # When upserting, row_data is not required
                return item
            row_data = item['row_data']
            if isinstance(row_data, str) and os.path.exists(row_data):
                item_url = client.upload_file(row_data)
                item['row_data'] = item_url
                if 'external_id' not in item:
                    # Default `external_id` to local file name
                    item['external_id'] = row_data
            return item

        def validate_attachments(item):
            attachments = item.get('attachments')
            if attachments:
                if isinstance(attachments, list):
                    if max_attachments_per_data_row and len(
                            attachments) > max_attachments_per_data_row:
                        raise ValueError(
                            f"Max attachments number of supported attachments per data row is {max_attachments_per_data_row}."
                            f" Found {len(attachments)}. Condense multiple attachments into one with the HTML attachment type if necessary."
                        )
                    for attachment in attachments:
                        AssetAttachment.validate_attachment_json(attachment)
                else:
                    raise ValueError(
                        f"Attachments must be a list. Found {type(attachments)}"
                    )
            return attachments

        def validate_embeddings(item):
            embeddings = item.get("embeddings")
            if embeddings:
                item["embeddings"] = [
                    EmbeddingVector(**e).to_gql() for e in embeddings
                ]

        def validate_conversational_data(conversational_data: list) -> None:
            """
            Checks each conversational message for keys expected as per https://docs.labelbox.com/reference/text-conversational#sample-conversational-json

            Args:
                conversational_data (list): list of dictionaries.
            """

            def check_message_keys(message):
                accepted_message_keys = set([
                    "messageId", "timestampUsec", "content", "user", "align",
                    "canLabel"
                ])
                for key in message.keys():
                    if not key in accepted_message_keys:
                        raise KeyError(
                            f"Invalid {key} key found! Accepted keys in messages list is {accepted_message_keys}"
                        )

            if conversational_data and not isinstance(conversational_data,
                                                      list):
                raise ValueError(
                    f"conversationalData must be a list. Found {type(conversational_data)}"
                )

            [check_message_keys(message) for message in conversational_data]

        def parse_metadata_fields(item):
            metadata_fields = item.get('metadata_fields')
            if metadata_fields:
                mdo = client.get_data_row_metadata_ontology()
                item['metadata_fields'] = mdo.parse_upsert_metadata(
                    metadata_fields)

        def format_row(item):
            # Formats user input into a consistent dict structure
            if isinstance(item, dict):
                # Convert fields to strings
                item = {
                    key.name if isinstance(key, Field) else key: value
                    for key, value in item.items()
                }
            elif isinstance(item, str):
                # The main advantage of using a string over a dict is that the user is specifying
                # that the file should exist locally.
                # That info is lost after this section so we should check for it here.
                if not os.path.exists(item):
                    raise ValueError(f"Filepath {item} does not exist.")
                item = {"row_data": item, "external_id": item}
            return item

        def validate_keys(item):
            if not is_upsert and 'row_data' not in item:
                raise InvalidQueryError(
                    "`row_data` missing when creating DataRow.")

            if isinstance(item.get('row_data'),
                          str) and item.get('row_data').startswith("s3:/"):
                raise InvalidQueryError(
                    "row_data: s3 assets must start with 'https'.")
            allowed_extra_fields = {
                'attachments', 'media_type', 'dataset_id', 'embeddings'
            }
            invalid_keys = set(item) - {f.name for f in DataRow.fields()
                                       } - allowed_extra_fields
            if invalid_keys:
                raise InvalidAttributeError(DataRow, invalid_keys)
            return item

        def formatLegacyConversationalData(item):
            messages = item.pop("conversationalData")
            version = item.pop("version", 1)
            type = item.pop("type", "application/vnd.labelbox.conversational")
            if "externalId" in item:
                external_id = item.pop("externalId")
                item["external_id"] = external_id
            if "globalKey" in item:
                global_key = item.pop("globalKey")
                item["globalKey"] = global_key
            validate_conversational_data(messages)
            one_conversation = \
                {
                    "type": type,
                    "version": version,
                    "messages": messages
                }
            item["row_data"] = one_conversation
            return item

        def convert_item(data_row_item):
            if isinstance(data_row_item, DataRowItemBase):
                item = data_row_item.payload
            else:
                item = data_row_item

            if "tileLayerUrl" in item:
                validate_attachments(item)
                return item

            if "conversationalData" in item:
                formatLegacyConversationalData(item)

            # Convert all payload variations into the same dict format
            item = format_row(item)
            # Make sure required keys exist (and there are no extra keys)
            validate_keys(item)
            # Make sure attachments are valid
            validate_attachments(item)
            # Make sure embeddings are valid
            validate_embeddings(item)
            # Parse metadata fields if they exist
            parse_metadata_fields(item)
            # Upload any local file paths
            item = upload_if_necessary(item)

            if isinstance(data_row_item, DataRowItemBase):
                return {'id': data_row_item.id, 'payload': item}
            else:
                return item

        if not isinstance(items, Iterable):
            raise ValueError(
                f"Must pass an iterable to create_data_rows. Found {type(items)}"
            )

        if len(items) > MAX_DATAROW_PER_API_OPERATION:
            raise MalformedQueryException(
                f"Cannot create more than {MAX_DATAROW_PER_API_OPERATION} DataRows per function call."
            )

        with ThreadPoolExecutor(file_upload_thread_count) as executor:
            futures = [executor.submit(convert_item, item) for item in items]
            items = [future.result() for future in as_completed(futures)]
        # Prepare and upload the desciptor file
        data = json.dumps(items)
        return client.upload_data(data,
                                  content_type="application/json",
                                  filename="json_import.json")

    @staticmethod
    def upload_in_chunks(client, specs: List[DataRowItemBase],
                         file_upload_thread_count: int,
                         upsert_chunk_size: int) -> UploadManifest:
        empty_specs = list(filter(lambda spec: spec.is_empty(), specs))

        if empty_specs:
            ids = list(map(lambda spec: spec.id.get("value"), empty_specs))
            raise ValueError(
                f"The following items have an empty payload: {ids}")

        chunks = [
            specs[i:i + upsert_chunk_size]
            for i in range(0, len(specs), upsert_chunk_size)
        ]

        def _upload_chunk(_chunk):
            return DataRowUploader.create_descriptor_file(client,
                                                          _chunk,
                                                          is_upsert=True)

        with ThreadPoolExecutor(file_upload_thread_count) as executor:
            futures = [
                executor.submit(_upload_chunk, chunk) for chunk in chunks
            ]
            chunk_uris = [future.result() for future in as_completed(futures)]

        return UploadManifest(source="SDK",
                              item_count=len(specs),
                              chunk_uris=chunk_uris)
