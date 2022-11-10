from typing import Generator, List, Union, Any, TYPE_CHECKING
import os
import json
import logging
from collections.abc import Iterable
import time
import ndjson
from itertools import islice

from concurrent.futures import ThreadPoolExecutor, as_completed
from io import StringIO
import requests

from labelbox import utils
from labelbox.exceptions import InvalidQueryError, LabelboxError, ResourceNotFoundError, InvalidAttributeError
from labelbox.orm.db_object import DbObject, Updateable, Deletable
from labelbox.orm.model import Entity, Field, Relationship
from labelbox.orm import query
from labelbox.exceptions import MalformedQueryException

if TYPE_CHECKING:
    from labelbox import Task, User, DataRow

logger = logging.getLogger(__name__)

MAX_DATAROW_PER_API_OPERATION = 150000
MAX_DATAROW_WITH_METADATA = 30000


class Dataset(DbObject, Updateable, Deletable):
    """ A Dataset is a collection of DataRows.

    Attributes:
        name (str)
        description (str)
        updated_at (datetime)
        created_at (datetime)
        row_count (int): The number of rows in the dataset. Fetch the dataset again to update since this is cached.

        projects (Relationship): `ToMany` relationship to Project
        data_rows (Relationship): `ToMany` relationship to DataRow
        created_by (Relationship): `ToOne` relationship to User
        organization (Relationship): `ToOne` relationship to Organization

    """
    name = Field.String("name")
    description = Field.String("description")
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    row_count = Field.Int("row_count")

    # Relationships
    projects = Relationship.ToMany("Project", True)
    data_rows = Relationship.ToMany("DataRow", False)
    created_by = Relationship.ToOne("User", False, "created_by")
    organization = Relationship.ToOne("Organization", False)
    iam_integration = Relationship.ToOne("IAMIntegration", False,
                                         "iam_integration", "signer")

    def create_data_row(self, items=None, **kwargs) -> "DataRow":
        """ Creates a single DataRow belonging to this dataset.

        >>> dataset.create_data_row(row_data="http://my_site.com/photos/img_01.jpg")

        Args:
            items: Dictionary containing new `DataRow` data. At a minimum,
                must contain `row_data` or `DataRow.row_data`.
            **kwargs: Key-value arguments containing new `DataRow` data. At a minimum,
                must contain `row_data`.

        Raises:
            InvalidQueryError: If both dictionary and `kwargs` are provided as inputs
            InvalidQueryError: If `DataRow.row_data` field value is not provided
                in `kwargs`.
            InvalidAttributeError: in case the DB object type does not contain
                any of the field names given in `kwargs`.

        """
        invalid_argument_error = "Argument to create_data_row() must be either a dictionary, or kwargs containing `row_data` at minimum"

        def convert_field_keys(items):
            if not isinstance(items, dict):
                raise InvalidQueryError(invalid_argument_error)
            return {
                key.name if isinstance(key, Field) else key: value
                for key, value in items.items()
            }

        if items is not None and len(kwargs) > 0:
            raise InvalidQueryError(invalid_argument_error)

        DataRow = Entity.DataRow
        args = convert_field_keys(items) if items is not None else kwargs

        if DataRow.row_data.name not in args:
            raise InvalidQueryError(
                "DataRow.row_data missing when creating DataRow.")

        row_data = args[DataRow.row_data.name]
        if not isinstance(row_data, str):
            # If the row data is an object, upload as a string
            args[DataRow.row_data.name] = json.dumps(row_data)
        elif os.path.exists(row_data):
            # If row data is a local file path, upload it to server.
            args[DataRow.row_data.name] = self.client.upload_file(row_data)

        # Parse metadata fields, if they are provided
        if DataRow.metadata_fields.name in args:
            mdo = self.client.get_data_row_metadata_ontology()
            args[DataRow.metadata_fields.name] = mdo.parse_upsert_metadata(
                args[DataRow.metadata_fields.name])

        query_str = """mutation CreateDataRowPyApi(
            $row_data: String!,
            $metadata_fields: [DataRowCustomMetadataUpsertInput!],
            $attachments: [DataRowAttachmentInput!],
            $media_type : MediaType,
            $external_id : String,
            $global_key : String,
            $dataset: ID!
            ){
                createDataRow(
                    data:
                      {
                        rowData: $row_data
                        mediaType: $media_type
                        metadataFields: $metadata_fields
                        externalId: $external_id
                        globalKey: $global_key
                        attachments: $attachments
                        dataset: {connect: {id: $dataset}}
                    }
                   )
                {%s}
            }
        """ % query.results_query_part(Entity.DataRow)
        res = self.client.execute(query_str, {**args, 'dataset': self.uid})
        return DataRow(self.client, res['createDataRow'])

    def create_data_rows_sync(self, items) -> None:
        """ Synchronously bulk upload data rows.

        Use this instead of `Dataset.create_data_rows` for smaller batches of data rows that need to be uploaded quickly.
        Cannot use this for uploads containing more than 1000 data rows.
        Each data row is also limited to 5 attachments.

        Args:
            items (iterable of (dict or str)):
                See the docstring for `Dataset._create_descriptor_file` for more information.
        Returns:
            None. If the function doesn't raise an exception then the import was successful.

        Raises:
            InvalidQueryError: If the `items` parameter does not conform to
                the specification in Dataset._create_descriptor_file or if the server did not accept the
                DataRow creation request (unknown reason).
            InvalidAttributeError: If there are fields in `items` not valid for
                a DataRow.
            ValueError: When the upload parameters are invalid
        """
        max_data_rows_supported = 1000
        max_attachments_per_data_row = 5
        if len(items) > max_data_rows_supported:
            raise ValueError(
                f"Dataset.create_data_rows_sync() supports a max of {max_data_rows_supported} data rows."
                " For larger imports use the async function Dataset.create_data_rows()"
            )
        descriptor_url = self._create_descriptor_file(
            items, max_attachments_per_data_row=max_attachments_per_data_row)
        dataset_param = "datasetId"
        url_param = "jsonUrl"
        query_str = """mutation AppendRowsToDatasetSyncPyApi($%s: ID!, $%s: String!){
            appendRowsToDatasetSync(data:{datasetId: $%s, jsonFileUrl: $%s}
            ){dataset{id}}} """ % (dataset_param, url_param, dataset_param,
                                   url_param)
        self.client.execute(query_str, {
            dataset_param: self.uid,
            url_param: descriptor_url
        })

    def create_data_rows(self, items) -> Union["Task", List[Any]]:
        """ Asynchronously bulk upload data rows

        Use this instead of `Dataset.create_data_rows_sync` uploads for batches that contain more than 1000 data rows.

        Args:
            items (iterable of (dict or str)): See the docstring for `Dataset._create_descriptor_file` for more information

        Returns:
            Task representing the data import on the server side. The Task
            can be used for inspecting task progress and waiting until it's done.

        Raises:
            InvalidQueryError: If the `items` parameter does not conform to
                the specification above or if the server did not accept the
                DataRow creation request (unknown reason).
            ResourceNotFoundError: If unable to retrieve the Task for the
                import process. This could imply that the import failed.
            InvalidAttributeError: If there are fields in `items` not valid for
                a DataRow.
            ValueError: When the upload parameters are invalid
        """
        descriptor_url = self._create_descriptor_file(items)
        # Create data source
        dataset_param = "datasetId"
        url_param = "jsonUrl"
        query_str = """mutation AppendRowsToDatasetPyApi($%s: ID!, $%s: String!){
            appendRowsToDataset(data:{datasetId: $%s, jsonFileUrl: $%s}
            ){ taskId accepted errorMessage } } """ % (dataset_param, url_param,
                                                       dataset_param, url_param)

        res = self.client.execute(query_str, {
            dataset_param: self.uid,
            url_param: descriptor_url
        })
        res = res["appendRowsToDataset"]
        if not res["accepted"]:
            msg = res['errorMessage']
            raise InvalidQueryError(
                f"Server did not accept DataRow creation request. {msg}")

        # Fetch and return the task.
        task_id = res["taskId"]
        user: User = self.client.get_user()
        tasks: List[Task] = list(
            user.created_tasks(where=Entity.Task.uid == task_id))
        # Cache user in a private variable as the relationship can't be
        # resolved due to server-side limitations (see Task.created_by)
        # for more info.
        if len(tasks) != 1:
            raise ResourceNotFoundError(Entity.Task, task_id)
        task: Task = tasks[0]
        task._user = user
        return task

    def _create_descriptor_file(self, items, max_attachments_per_data_row=None):
        """
        This function is shared by both `Dataset.create_data_rows` and `Dataset.create_data_rows_sync`
        to prepare the input file. The user defined input is validated, processed, and json stringified.
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
            row_data = item['row_data']
            if isinstance(row_data, str) and os.path.exists(row_data):
                item_url = self.client.upload_file(row_data)
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
                mdo = self.client.get_data_row_metadata_ontology()
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
            if 'row_data' not in item:
                raise InvalidQueryError(
                    "`row_data` missing when creating DataRow.")

            invalid_keys = set(item) - {
                *{f.name for f in DataRow.fields()}, 'attachments', 'media_type'
            }
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

        def convert_item(item):
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
            # Parse metadata fields if they exist
            parse_metadata_fields(item)
            # Upload any local file paths
            item = upload_if_necessary(item)
            return item

        if not isinstance(items, Iterable):
            raise ValueError(
                f"Must pass an iterable to create_data_rows. Found {type(items)}"
            )

        if len(items) > MAX_DATAROW_PER_API_OPERATION:
            raise MalformedQueryException(
                f"Cannot create more than {MAX_DATAROW_PER_API_OPERATION} DataRows per function call."
            )

        # TODO: If any datarows contain metadata, we're limiting max # of datarows
        # until we address performance issues with datarow create with metadata
        if len(items) > MAX_DATAROW_WITH_METADATA:
            for row in items:
                if 'metadata_fields' in row:
                    raise MalformedQueryException(
                        f"Cannot create more than {MAX_DATAROW_WITH_METADATA} DataRows, if any DataRows contain metadata"
                    )

        with ThreadPoolExecutor(file_upload_thread_count) as executor:
            futures = [executor.submit(convert_item, item) for item in items]
            items = [future.result() for future in as_completed(futures)]
        # Prepare and upload the desciptor file
        data = json.dumps(items)
        return self.client.upload_data(data,
                                       content_type="application/json",
                                       filename="json_import.json")

    def data_rows_for_external_id(self,
                                  external_id,
                                  limit=10) -> List["DataRow"]:
        """ Convenience method for getting a multiple `DataRow` belonging to this
        `Dataset` that has the given `external_id`.

        Args:
            external_id (str): External ID of the sought `DataRow`.
            limit (int): The maximum number of data rows to return for the given external_id

        Returns:
            A list of `DataRow` with the given ID.

        Raises:
            labelbox.exceptions.ResourceNotFoundError: If there is no `DataRow`
                in this `DataSet` with the given external ID, or if there are
                multiple `DataRows` for it.
        """
        DataRow = Entity.DataRow
        where = DataRow.external_id == external_id

        data_rows = self.data_rows(where=where)
        # Get at most `limit` data_rows.
        data_rows = list(islice(data_rows, limit))

        if not len(data_rows):
            raise ResourceNotFoundError(DataRow, where)
        return data_rows

    def data_row_for_external_id(self, external_id) -> "DataRow":
        """ Convenience method for getting a single `DataRow` belonging to this
        `Dataset` that has the given `external_id`.

        Args:
            external_id (str): External ID of the sought `DataRow`.

        Returns:
            A single `DataRow` with the given ID.

        Raises:
            labelbox.exceptions.ResourceNotFoundError: If there is no `DataRow`
                in this `DataSet` with the given external ID, or if there are
                multiple `DataRows` for it.
        """
        data_rows = self.data_rows_for_external_id(external_id=external_id,
                                                   limit=2)
        if len(data_rows) > 1:
            logger.warning(
                f"More than one data_row has the provided external_id : `%s`. Use function data_rows_for_external_id to fetch all",
                external_id)
        return data_rows[0]

    def export_data_rows(self,
                         timeout_seconds=120,
                         include_metadata: bool = False) -> Generator:
        """ Returns a generator that produces all data rows that are currently
        attached to this dataset.

        Note: For efficiency, the data are cached for 30 minutes. Newly created data rows will not appear
        until the end of the cache period.

        Args:
            timeout_seconds (float): Max waiting time, in seconds.
            include_metadata (bool): True to return related DataRow metadata
        Returns:
            Generator that yields DataRow objects belonging to this dataset.
        Raises:
            LabelboxError: if the export fails or is unable to download within the specified time.
        """
        id_param = "datasetId"
        metadata_param = "includeMetadataInput"
        query_str = """mutation GetDatasetDataRowsExportUrlPyApi($%s: ID!, $%s: Boolean!)
            {exportDatasetDataRows(data:{datasetId: $%s , includeMetadataInput: $%s}) {downloadUrl createdAt status}}
        """ % (id_param, metadata_param, id_param, metadata_param)
        sleep_time = 2
        while True:
            res = self.client.execute(query_str, {
                id_param: self.uid,
                metadata_param: include_metadata
            })
            res = res["exportDatasetDataRows"]
            if res["status"] == "COMPLETE":
                download_url = res["downloadUrl"]
                response = requests.get(download_url)
                response.raise_for_status()
                reader = ndjson.reader(StringIO(response.text))
                return (
                    Entity.DataRow(self.client, result) for result in reader)
            elif res["status"] == "FAILED":
                raise LabelboxError("Data row export failed.")

            timeout_seconds -= sleep_time
            if timeout_seconds <= 0:
                raise LabelboxError(
                    f"Unable to export data rows within {timeout_seconds} seconds."
                )

            logger.debug("Dataset '%s' data row export, waiting for server...",
                         self.uid)
            time.sleep(sleep_time)
