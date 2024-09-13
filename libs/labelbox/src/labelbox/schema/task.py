import json
import logging
import requests
import time
from typing import TYPE_CHECKING, Callable, Optional, Dict, Any, List, Union
from labelbox import parser

from labelbox.exceptions import ResourceNotFoundError
from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field, Relationship, Entity

from labelbox.pagination import PaginatedCollection
from labelbox.schema.internal.datarow_upload_constants import (
    DOWNLOAD_RESULT_PAGE_SIZE,
)

if TYPE_CHECKING:
    from labelbox import User

    def lru_cache() -> Callable[..., Callable[..., Dict[str, Any]]]:
        pass
else:
    from functools import lru_cache

logger = logging.getLogger(__name__)


class Task(DbObject):
    """Represents a server-side process that might take a longer time to process.
    Allows the Task state to be updated and checked on the client side.

    Attributes:
        updated_at (datetime)
        created_at (datetime)
        name (str)
        status (str)
        completion_percentage (float)

        created_by (Relationship): `ToOne` relationship to User
        organization (Relationship): `ToOne` relationship to Organization
    """

    updated_at = Field.DateTime("updated_at")
    created_at = Field.DateTime("created_at")
    name = Field.String("name")
    status = Field.String("status")
    completion_percentage = Field.Float("completion_percentage")
    result_url = Field.String("result_url", "result")
    errors_url = Field.String("errors_url", "errors")
    type = Field.String("type")
    metadata = Field.Json("metadata")
    _user: Optional["User"] = None

    # Relationships
    created_by = Relationship.ToOne("User", False, "created_by")
    organization = Relationship.ToOne("Organization")

    def __eq__(self, task):
        return (
            isinstance(task, Task)
            and task.uid == self.uid
            and task.type == self.type
        )

    def __hash__(self):
        return hash(self.uid)

    # Import and upsert have several instances of special casing
    def is_creation_task(self) -> bool:
        return self.name == "JSON Import" or self.type == "adv-upsert-data-rows"

    def refresh(self) -> None:
        """Refreshes Task data from the server."""
        assert self._user is not None
        tasks = list(self._user.created_tasks(where=Task.uid == self.uid))
        if len(tasks) != 1:
            raise ResourceNotFoundError(Task, self.uid)
        for field in self.fields():
            setattr(self, field.name, getattr(tasks[0], field.name))
            if self.is_creation_task():
                self.errors_url = self.result_url

    def has_errors(self) -> bool:
        if self.type == "export-data-rows":
            # self.errors fetches the error content.
            # This first condition prevents us from downloading the content for v2 exports
            return bool(self.errors_url or self.errors)
        if self.is_creation_task():
            return bool(self.failed_data_rows)
        return self.status == "FAILED"

    def wait_until_done(
        self, timeout_seconds: float = 300.0, check_frequency: float = 2.0
    ) -> None:
        self.wait_till_done(timeout_seconds, check_frequency)

    def wait_till_done(
        self, timeout_seconds: float = 300.0, check_frequency: float = 2.0
    ) -> None:
        """Waits until the task is completed. Periodically queries the server
        to update the task attributes.

        Args:
            timeout_seconds (float): Maximum time this method can block, in seconds. Defaults to five minutes.
            check_frequency (float): Frequency of queries to server to update the task attributes, in seconds. Defaults to two seconds. Minimal value is two seconds.
        """
        if check_frequency < 2.0:
            raise ValueError(
                "Expected check frequency to be two seconds or more"
            )
        while timeout_seconds > 0:
            if self.status != "IN_PROGRESS":
                if self.has_errors():
                    logger.warning(
                        "There are errors present. Please look at `task.errors` for more details"
                    )
                return
            logger.debug(
                "Task.wait_till_done sleeping for %d seconds", check_frequency
            )
            time.sleep(check_frequency)
            timeout_seconds -= check_frequency
            self.refresh()

    @property
    def errors(self) -> Optional[Dict[str, Any]]:
        """Fetch the error associated with an import task."""
        if self.is_creation_task():
            if self.status == "FAILED":
                result = self._fetch_remote_json()
                return result["error"]
            elif self.status == "COMPLETE":
                return self.failed_data_rows
        elif self.type == "export-data-rows":
            return self._fetch_remote_json(remote_json_field="errors_url")
        elif (
            self.type == "add-data-rows-to-batch"
            or self.type == "send-to-task-queue"
            or self.type == "send-to-annotate"
        ):
            if self.status == "FAILED":
                # for these tasks, the error is embedded in the result itself
                return json.loads(self.result_url)
        return None

    @property
    def result(self) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """Fetch the result for an import task."""
        if self.status == "FAILED":
            raise ValueError(f"Job failed. Errors : {self.errors}")
        else:
            result = self._fetch_remote_json()
            if self.type == "export-data-rows":
                return result

            return [
                {
                    "id": data_row["id"],
                    "external_id": data_row.get("externalId"),
                    "row_data": data_row["rowData"],
                    "global_key": data_row.get("globalKey"),
                }
                for data_row in result["createdDataRows"]
            ]

    @property
    def failed_data_rows(self) -> Optional[Dict[str, Any]]:
        """Fetch data rows which failed to be created for an import task."""
        result = self._fetch_remote_json()
        if len(result.get("errors", [])) > 0:
            return result["errors"]
        else:
            return None

    @property
    def created_data_rows(self) -> Optional[Dict[str, Any]]:
        """Fetch data rows which successfully created for an import task."""
        result = self._fetch_remote_json()
        if len(result.get("createdDataRows", [])) > 0:
            return result["createdDataRows"]
        else:
            return None

    @lru_cache()
    def _fetch_remote_json(
        self, remote_json_field: Optional[str] = None
    ) -> Dict[str, Any]:
        """Function for fetching and caching the result data."""

        def download_result(remote_json_field: Optional[str], format: str):
            url = getattr(self, remote_json_field or "result_url")

            if url is None:
                return None

            response = requests.get(url)
            response.raise_for_status()
            if format == "json":
                return response.json()
            elif format == "ndjson":
                return parser.loads(response.text)
            else:
                raise ValueError(
                    "Expected the result format to be either `ndjson` or `json`."
                )

        if self.is_creation_task():
            format = "json"
        elif self.type == "export-data-rows":
            format = "ndjson"
        else:
            raise ValueError(
                "Task result is only supported for `JSON Import` and `export` tasks."
                " Download task.result_url manually to access the result for other tasks."
            )

        if self.status != "IN_PROGRESS":
            return download_result(remote_json_field, format)
        else:
            self.wait_till_done(timeout_seconds=600)
            if self.status == "IN_PROGRESS":
                raise ValueError(
                    "Job status still in `IN_PROGRESS`. The result is not available. Call task.wait_till_done() with a larger timeout or contact support."
                )
            return download_result(remote_json_field, format)

    @staticmethod
    def get_task(client, task_id):
        user: User = client.get_user()
        tasks: List[Task] = list(
            user.created_tasks(where=Entity.Task.uid == task_id)
        )
        # Cache user in a private variable as the relationship can't be
        # resolved due to server-side limitations (see Task.created_by)
        # for more info.
        if len(tasks) != 1:
            raise ResourceNotFoundError(Entity.Task, {task_id: task_id})
        task: Task = tasks[0]
        task._user = user
        return task


class DataUpsertTask(Task):
    """
    Task class for data row upsert operations
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user = None

    @property
    def result(self) -> Optional[List[Dict[str, Any]]]:  # type: ignore
        """
        Fetches all results.
        Note, for large uploads (>150K data rows), it could take multiple minutes to complete
        """
        if self.status == "FAILED":
            raise ValueError(f"Job failed. Errors : {self.errors}")
        return self._results_as_list()

    @property
    def errors(self) -> Optional[List[Dict[str, Any]]]:  # type: ignore
        """
        Fetches all errors.
        Note, for large uploads / large number of errors (>150K), it could take multiple minutes to complete
        """
        return self._errors_as_list()

    @property
    def created_data_rows(  # type: ignore
        self,
    ) -> Optional[List[Dict[str, Any]]]:
        return self.result

    @property
    def failed_data_rows(  # type: ignore
        self,
    ) -> Optional[List[Dict[str, Any]]]:
        return self.errors

    def _download_results_paginated(self) -> PaginatedCollection:
        page_size = DOWNLOAD_RESULT_PAGE_SIZE
        from_cursor = None

        query_str = """query SuccessesfulDataRowImportsPyApi($taskId: ID!, $first: Int, $from: String)  {
                    successesfulDataRowImports(data: { taskId: $taskId, first: $first, from: $from})
                        {
                            nodes { 
                                id
                                externalId
                                globalKey
                                rowData
                                }
                            after
                            total
                        }
                    }
                """

        params = {
            "taskId": self.uid,
            "first": page_size,
            "from": from_cursor,
        }

        return PaginatedCollection(
            client=self.client,
            query=query_str,
            params=params,
            dereferencing=["successesfulDataRowImports", "nodes"],
            obj_class=lambda _, data_row: {
                "id": data_row.get("id"),
                "external_id": data_row.get("externalId"),
                "row_data": data_row.get("rowData"),
                "global_key": data_row.get("globalKey"),
            },
            cursor_path=["successesfulDataRowImports", "after"],
        )

    def _download_errors_paginated(self) -> PaginatedCollection:
        page_size = DOWNLOAD_RESULT_PAGE_SIZE  # hardcode to avoid overloading the server
        from_cursor = None

        query_str = """query FailedDataRowImportsPyApi($taskId: ID!, $first: Int, $from: String)  {
                    failedDataRowImports(data: { taskId: $taskId, first: $first, from: $from})
                        {
                            after
                            total
                            results {
                                message
                                spec {
                                    externalId
                                    globalKey
                                    rowData
                                        metadata {
                                            schemaId
                                            value
                                            name
                                        }
                                        attachments {
                                            type
                                            value
                                            name
                                        }                                    
                                }
                            }
                        }
                    }
                """

        params = {
            "taskId": self.uid,
            "first": page_size,
            "from": from_cursor,
        }

        def convert_errors_to_legacy_format(client, data_row):
            spec = data_row.get("spec", {})
            return {
                "message": data_row.get("message"),
                "failedDataRows": [
                    {
                        "externalId": spec.get("externalId"),
                        "rowData": spec.get("rowData"),
                        "globalKey": spec.get("globalKey"),
                        "metadata": spec.get("metadata", []),
                        "attachments": spec.get("attachments", []),
                    }
                ],
            }

        return PaginatedCollection(
            client=self.client,
            query=query_str,
            params=params,
            dereferencing=["failedDataRowImports", "results"],
            obj_class=convert_errors_to_legacy_format,
            cursor_path=["failedDataRowImports", "after"],
        )

    def _results_as_list(self) -> Optional[List[Dict[str, Any]]]:
        total_downloaded = 0
        results = []
        data = self._download_results_paginated()

        for row in data:
            results.append(row)
            total_downloaded += 1

        if len(results) == 0:
            return None

        return results

    def _errors_as_list(self) -> Optional[List[Dict[str, Any]]]:
        total_downloaded = 0
        errors = []
        data = self._download_errors_paginated()

        for row in data:
            errors.append(row)
            total_downloaded += 1

        if len(errors) == 0:
            return None

        return errors
