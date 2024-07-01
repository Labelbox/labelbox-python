from datetime import datetime
from typing import Dict, Generator, List, Optional, Any, Final, Tuple, Union
import os
import json
import logging
from collections.abc import Iterable
from string import Template
import time
import warnings

from labelbox import parser
from itertools import islice

from concurrent.futures import ThreadPoolExecutor, as_completed
from io import StringIO
import requests

from labelbox.exceptions import InvalidQueryError, LabelboxError, ResourceNotFoundError, ResourceCreationError
from labelbox.orm.comparison import Comparison
from labelbox.orm.db_object import DbObject, Updateable, Deletable, experimental
from labelbox.orm.model import Entity, Field, Relationship
from labelbox.orm import query
from labelbox.exceptions import MalformedQueryException
from labelbox.pagination import PaginatedCollection
from labelbox.pydantic_compat import BaseModel
from labelbox.schema.data_row import DataRow
from labelbox.schema.embedding import EmbeddingVector
from labelbox.schema.export_filters import DatasetExportFilters, build_filters
from labelbox.schema.export_params import CatalogExportParams, validate_catalog_export_params
from labelbox.schema.export_task import ExportTask
from labelbox.schema.identifiable import UniqueId, GlobalKey
from labelbox.schema.task import Task, DataUpsertTask
from labelbox.schema.user import User
from labelbox.schema.iam_integration import IAMIntegration
from labelbox.schema.internal.data_row_upsert_item import (DataRowItemBase,
                                                           DataRowUpsertItem,
                                                           DataRowCreateItem)
import labelbox.schema.internal.data_row_uploader as data_row_uploader
from labelbox.schema.internal.descriptor_file_creator import DescriptorFileCreator
from labelbox.schema.internal.datarow_upload_constants import (
    FILE_UPLOAD_THREAD_COUNT, UPSERT_CHUNK_SIZE_BYTES)

logger = logging.getLogger(__name__)


class Dataset(DbObject, Updateable, Deletable):
    """ A Dataset is a collection of DataRows.

    Attributes:
        name (str)
        description (str)
        updated_at (datetime)
        created_at (datetime)
        row_count (int): The number of rows in the dataset. Fetch the dataset again to update since this is cached.

        created_by (Relationship): `ToOne` relationship to User
        organization (Relationship): `ToOne` relationship to Organization
    """

    name = Field.String("name")
    description = Field.String("description")
    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    row_count = Field.Int("row_count")

    # Relationships
    created_by = Relationship.ToOne("User", False, "created_by")
    organization = Relationship.ToOne("Organization", False)
    iam_integration = Relationship.ToOne("IAMIntegration", False,
                                         "iam_integration", "signer")

    def data_rows(
        self,
        from_cursor: Optional[str] = None,
        where: Optional[Comparison] = None,
    ) -> PaginatedCollection:
        """
        Custom method to paginate data_rows via cursor.

        Args:
            from_cursor (str): Cursor (data row id) to start from, if none, will start from the beginning
            where (dict(str,str)): Filter to apply to data rows. Where value is a data row column name and key is the value to filter on.
            example: {'external_id': 'my_external_id'} to get a data row with external_id = 'my_external_id'


        NOTE:
            Order of retrieval is newest data row first.
            Deleted data rows are not retrieved.
            Failed data rows are not retrieved.
            Data rows in progress *maybe* retrieved.
        """

        page_size = 500  # hardcode to avoid overloading the server
        where_param = query.where_as_dict(Entity.DataRow,
                                          where) if where is not None else None

        template = Template(
            """query DatasetDataRowsPyApi($$id: ID!, $$from: ID, $$first: Int, $$where: DatasetDataRowWhereInput)  {
                        datasetDataRows(id: $$id, from: $$from, first: $$first, where: $$where)
                            {
                                nodes { $datarow_selections }
                                pageInfo { hasNextPage startCursor }
                            }
                        }
                    """)
        query_str = template.substitute(
            datarow_selections=query.results_query_part(Entity.DataRow))

        params = {
            'id': self.uid,
            'from': from_cursor,
            'first': page_size,
            'where': where_param,
        }

        return PaginatedCollection(
            client=self.client,
            query=query_str,
            params=params,
            dereferencing=['datasetDataRows', 'nodes'],
            obj_class=Entity.DataRow,
            cursor_path=['datasetDataRows', 'pageInfo', 'startCursor'],
        )

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
            ResourceCreationError: If data row creation failed on the server side.
        """
        invalid_argument_error = "Argument to create_data_row() must be either a dictionary, or kwargs containing `row_data` at minimum"

        if items is not None and len(kwargs) > 0:
            raise InvalidQueryError(invalid_argument_error)

        args = items if items is not None else kwargs

        file_upload_thread_count = 1
        completed_task = self._create_data_rows_sync(
            [args], file_upload_thread_count=file_upload_thread_count)

        res = completed_task.result
        if res is None or len(res) == 0:
            raise ResourceCreationError(
                f"Data row upload did not complete, task status {completed_task.status} task id {completed_task.uid}"
            )

        return self.client.get_data_row(res[0]['id'])

    def create_data_rows_sync(
            self,
            items,
            file_upload_thread_count=FILE_UPLOAD_THREAD_COUNT) -> None:
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
            ResourceCreationError: If the `items` parameter does not conform to
                the specification in Dataset._create_descriptor_file or if the server did not accept the
                DataRow creation request (unknown reason).
            InvalidAttributeError: If there are fields in `items` not valid for
                a DataRow.
            ValueError: When the upload parameters are invalid
        """
        warnings.warn(
            "This method is deprecated and will be "
            "removed in a future release. Please use create_data_rows instead.")

        self._create_data_rows_sync(
            items, file_upload_thread_count=file_upload_thread_count)

        return None  # Return None if no exception is raised

    def _create_data_rows_sync(self,
                               items,
                               file_upload_thread_count=FILE_UPLOAD_THREAD_COUNT
                              ) -> "DataUpsertTask":
        max_data_rows_supported = 1000
        if len(items) > max_data_rows_supported:
            raise ValueError(
                f"Dataset.create_data_rows_sync() supports a max of {max_data_rows_supported} data rows."
                " For larger imports use the async function Dataset.create_data_rows()"
            )
        if file_upload_thread_count < 1:
            raise ValueError(
                "file_upload_thread_count must be a positive integer")

        task: DataUpsertTask = self.create_data_rows(items,
                                                     file_upload_thread_count)
        task.wait_till_done()

        if task.has_errors():
            raise ResourceCreationError(
                f"Data row upload errors: {task.errors}", cause=task.uid)
        if task.status != "COMPLETE":
            raise ResourceCreationError(
                f"Data row upload did not complete, task status {task.status} task id {task.uid}"
            )

        return task

    def create_data_rows(self,
                         items,
                         file_upload_thread_count=FILE_UPLOAD_THREAD_COUNT
                        ) -> "DataUpsertTask":
        """ Asynchronously bulk upload data rows

        Use this instead of `Dataset.create_data_rows_sync` uploads for batches that contain more than 1000 data rows.

        Args:
            items (iterable of (dict or str))

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

        NOTE  dicts and strings items can not be mixed in the same call. It is a responsibility of the caller to ensure that all items are of the same type.
        """

        if file_upload_thread_count < 1:
            raise ValueError(
                "file_upload_thread_count must be a positive integer")

        # Usage example
        upload_items = self._separate_and_process_items(items)
        specs = DataRowCreateItem.build(self.uid, upload_items)
        return self._exec_upsert_data_rows(specs, file_upload_thread_count)

    def _separate_and_process_items(self, items):
        string_items = [item for item in items if isinstance(item, str)]
        dict_items = [item for item in items if isinstance(item, dict)]
        dict_string_items = []
        if len(string_items) > 0:
            dict_string_items = self._build_from_local_paths(string_items)
        return dict_items + dict_string_items

    def _build_from_local_paths(
            self,
            items: List[str],
            file_upload_thread_count=FILE_UPLOAD_THREAD_COUNT) -> List[dict]:
        uploaded_items = []

        def upload_file(item):
            item_url = self.client.upload_file(item)
            return {'row_data': item_url, 'external_id': item}

        with ThreadPoolExecutor(file_upload_thread_count) as executor:
            futures = [
                executor.submit(upload_file, item)
                for item in items
                if isinstance(item, str) and os.path.exists(item)
            ]
            more_items = [future.result() for future in as_completed(futures)]
            uploaded_items.extend(more_items)

        return uploaded_items

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
        at_most_data_rows = list(islice(data_rows, limit))

        if not len(at_most_data_rows):
            raise ResourceNotFoundError(DataRow, where)
        return at_most_data_rows

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
        warnings.warn(
            "You are currently utilizing exports v1 for this action, which will be deprecated after April 30th, 2024. We recommend transitioning to exports v2. To view export v2 details, visit our docs: https://docs.labelbox.com/reference/label-export",
            DeprecationWarning)
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
                reader = parser.reader(StringIO(response.text))
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

    def export(
        self,
        task_name: Optional[str] = None,
        filters: Optional[DatasetExportFilters] = None,
        params: Optional[CatalogExportParams] = None,
    ) -> ExportTask:
        """
        Creates a dataset export task with the given params and returns the task.

        >>>     dataset = client.get_dataset(DATASET_ID)
        >>>     task = dataset.export(
        >>>         filters={
        >>>             "last_activity_at": ["2000-01-01 00:00:00", "2050-01-01 00:00:00"],
        >>>             "label_created_at": ["2000-01-01 00:00:00", "2050-01-01 00:00:00"],
        >>>             "data_row_ids": [DATA_ROW_ID_1, DATA_ROW_ID_2, ...] # or global_keys: [DATA_ROW_GLOBAL_KEY_1, DATA_ROW_GLOBAL_KEY_2, ...]
        >>>         },
        >>>         params={
        >>>             "performance_details": False,
        >>>             "label_details": True
        >>>         })
        >>>     task.wait_till_done()
        >>>     task.result
        """
        task, _ = self._export(task_name, filters, params, streamable=True)
        return ExportTask(task)

    def export_v2(
        self,
        task_name: Optional[str] = None,
        filters: Optional[DatasetExportFilters] = None,
        params: Optional[CatalogExportParams] = None,
    ) -> Union[Task, ExportTask]:
        """
        Creates a dataset export task with the given params and returns the task.

        >>>     dataset = client.get_dataset(DATASET_ID)
        >>>     task = dataset.export_v2(
        >>>         filters={
        >>>             "last_activity_at": ["2000-01-01 00:00:00", "2050-01-01 00:00:00"],
        >>>             "label_created_at": ["2000-01-01 00:00:00", "2050-01-01 00:00:00"],
        >>>             "data_row_ids": [DATA_ROW_ID_1, DATA_ROW_ID_2, ...] # or global_keys: [DATA_ROW_GLOBAL_KEY_1, DATA_ROW_GLOBAL_KEY_2, ...]
        >>>         },
        >>>         params={
        >>>             "performance_details": False,
        >>>             "label_details": True
        >>>         })
        >>>     task.wait_till_done()
        >>>     task.result
        """
        task, is_streamable = self._export(task_name, filters, params)
        if (is_streamable):
            return ExportTask(task, True)
        return task

    def _export(
        self,
        task_name: Optional[str] = None,
        filters: Optional[DatasetExportFilters] = None,
        params: Optional[CatalogExportParams] = None,
        streamable: bool = False,
    ) -> Tuple[Task, bool]:
        _params = params or CatalogExportParams({
            "attachments": False,
            "embeddings": False,
            "metadata_fields": False,
            "data_row_details": False,
            "project_details": False,
            "performance_details": False,
            "label_details": False,
            "media_type_override": None,
            "model_run_ids": None,
            "project_ids": None,
            "interpolated_frames": False,
            "all_projects": False,
            "all_model_runs": False,
        })
        validate_catalog_export_params(_params)

        _filters = filters or DatasetExportFilters({
            "last_activity_at": None,
            "label_created_at": None,
            "data_row_ids": None,
            "global_keys": None,
        })

        mutation_name = "exportDataRowsInCatalog"
        create_task_query_str = (
            f"mutation {mutation_name}PyApi"
            f"($input: ExportDataRowsInCatalogInput!)"
            f"{{{mutation_name}(input: $input){{taskId isStreamable}}}}")
        media_type_override = _params.get('media_type_override', None)

        if task_name is None:
            task_name = f"Export v2: dataset - {self.name}"
        query_params: Dict[str, Any] = {
            "input": {
                "taskName": task_name,
                "filters": {
                    "searchQuery": {
                        "scope": None,
                        "query": None,
                    }
                },
                "isStreamableReady": True,
                "params": {
                    "mediaTypeOverride":
                        media_type_override.value
                        if media_type_override is not None else None,
                    "includeAttachments":
                        _params.get('attachments', False),
                    "includeEmbeddings":
                        _params.get('embeddings', False),
                    "includeMetadata":
                        _params.get('metadata_fields', False),
                    "includeDataRowDetails":
                        _params.get('data_row_details', False),
                    "includeProjectDetails":
                        _params.get('project_details', False),
                    "includePerformanceDetails":
                        _params.get('performance_details', False),
                    "includeLabelDetails":
                        _params.get('label_details', False),
                    "includeInterpolatedFrames":
                        _params.get('interpolated_frames', False),
                    "includePredictions":
                        _params.get('predictions', False),
                    "projectIds":
                        _params.get('project_ids', None),
                    "modelRunIds":
                        _params.get('model_run_ids', None),
                    "allProjects":
                        _params.get('all_projects', False),
                    "allModelRuns":
                        _params.get('all_model_runs', False),
                },
                "streamable": streamable,
            }
        }

        search_query = build_filters(self.client, _filters)
        search_query.append({
            "ids": [self.uid],
            "operator": "is",
            "type": "dataset"
        })

        query_params["input"]["filters"]["searchQuery"]["query"] = search_query

        res = self.client.execute(create_task_query_str,
                                  query_params,
                                  error_log_key="errors")
        res = res[mutation_name]
        task_id = res["taskId"]
        is_streamable = res["isStreamable"]
        return Task.get_task(self.client, task_id), is_streamable

    def upsert_data_rows(self,
                         items,
                         file_upload_thread_count=FILE_UPLOAD_THREAD_COUNT
                        ) -> "DataUpsertTask":
        """
        Upserts data rows in this dataset. When "key" is provided, and it references an existing data row,
        an update will be performed. When "key" is not provided a new data row will be created.

        >>>     task = dataset.upsert_data_rows([
        >>>         # create new data row
        >>>         {
        >>>             "row_data": "http://my_site.com/photos/img_01.jpg",
        >>>             "global_key": "global_key1",
        >>>             "external_id": "ex_id1",
        >>>             "attachments": [
        >>>                 {"type": AttachmentType.RAW_TEXT, "name": "att1", "value": "test1"}
        >>>             ],
        >>>             "metadata": [
        >>>                 {"name": "tag", "value": "tag value"},
        >>>             ]
        >>>         },
        >>>         # update global key of data row by existing global key
        >>>         {
        >>>             "key": GlobalKey("global_key1"),
        >>>             "global_key": "global_key1_updated"
        >>>         },
        >>>         # update data row by ID
        >>>         {
        >>>             "key": UniqueId(dr.uid),
        >>>             "external_id": "ex_id1_updated"
        >>>         },
        >>>     ])
        >>>     task.wait_till_done()
        """
        specs = DataRowUpsertItem.build(self.uid, items, (UniqueId, GlobalKey))
        return self._exec_upsert_data_rows(specs, file_upload_thread_count)

    def _exec_upsert_data_rows(
        self,
        specs: List[DataRowItemBase],
        file_upload_thread_count: int = FILE_UPLOAD_THREAD_COUNT
    ) -> "DataUpsertTask":

        manifest = data_row_uploader.upload_in_chunks(
            client=self.client,
            specs=specs,
            file_upload_thread_count=file_upload_thread_count,
            max_chunk_size_bytes=UPSERT_CHUNK_SIZE_BYTES)

        data = json.dumps(manifest.dict()).encode("utf-8")
        manifest_uri = self.client.upload_data(data,
                                               content_type="application/json",
                                               filename="manifest.json")

        query_str = """
            mutation UpsertDataRowsPyApi($manifestUri: String!) {
                upsertDataRows(data: { manifestUri: $manifestUri }) { 
                    id createdAt updatedAt name status completionPercentage result errors type metadata 
                }
            }
            """

        res = self.client.execute(query_str, {"manifestUri": manifest_uri})
        res = res["upsertDataRows"]
        task = DataUpsertTask(self.client, res)
        task._user = self.client.get_user()
        return task

    def add_iam_integration(
            self, iam_integration: Union[str,
                                         IAMIntegration]) -> IAMIntegration:
        """          
        Sets the IAM integration for the dataset. IAM integration is used to sign URLs for data row assets.

    Args:
            iam_integration (Union[str, IAMIntegration]): IAM integration object or IAM integration id.

        Returns:
            IAMIntegration: IAM integration object.

        Raises:
            LabelboxError: If the IAM integration can't be set.

        Examples:
        
            >>>    # Get all IAM integrations
            >>>    iam_integrations = client.get_organization().get_iam_integrations()
            >>>    
            >>>    # Get IAM integration id
            >>>    iam_integration_id = [integration.uid for integration
            >>>      in iam_integrations
            >>>      if integration.name == "My S3 integration"][0]
            >>>
            >>>   # Set IAM integration for integration id
            >>>   dataset.set_iam_integration(iam_integration_id)
            >>>
            >>>    # Get IAM integration object
            >>>    iam_integration = [integration.uid for integration
            >>>      in iam_integrations
            >>>      if integration.name == "My S3 integration"][0]
            >>>
            >>>   # Set IAM integration for IAMIntegrtion object
            >>>   dataset.set_iam_integration(iam_integration)
        """

        iam_integration_id = iam_integration.uid if isinstance(
            iam_integration, IAMIntegration) else iam_integration

        query = """
            mutation SetSignerForDatasetPyApi($signerId: ID!, $datasetId: ID!) {
                setSignerForDataset(
                    data: { signerId: $signerId }
                    where: { id: $datasetId }
                ) {
                    id
                    signer {
                        id
                    }
                }
            }
        """

        response = self.client.execute(query, {
            "signerId": iam_integration_id,
            "datasetId": self.uid
        })

        if not response:
            raise ResourceNotFoundError(IAMIntegration, {
                "signerId": iam_integration_id,
                "datasetId": self.uid
            })

        try:
            iam_integration_id = response.get("setSignerForDataset",
                                              {}).get("signer", {})["id"]

            return [
                integration for integration in
                self.client.get_organization().get_iam_integrations()
                if integration.uid == iam_integration_id
            ][0]
        except:
            raise LabelboxError(
                f"Can't retrieve IAM integration {iam_integration_id}")

    def remove_iam_integration(self) -> None:
        """
        Unsets the IAM integration for the dataset.

        Args:
            None

        Returns:
            None

        Raises:
            LabelboxError: If the IAM integration can't be unset.

        Examples:
            >>> dataset.remove_iam_integration()
        """

        query = """
        mutation DetachSignerPyApi($id: ID!) {
            clearSignerForDataset(where: { id: $id }) {
                id
            }
        }
        """

        response = self.client.execute(query, {"id": self.uid})

        if not response:
            raise ResourceNotFoundError(Dataset, {"id": self.uid})
