import logging
import json
import requests
import time
from typing import TYPE_CHECKING, TypeVar, Callable, Optional, Dict, Any, List

from labelbox.exceptions import ResourceNotFoundError
from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field, Relationship

if TYPE_CHECKING:
    from labelbox import User

    def lru_cache() -> Callable[..., Callable[..., Dict[str, Any]]]:
        pass
else:
    from functools import lru_cache

logger = logging.getLogger(__name__)


class Task(DbObject):
    """ Represents a server-side process that might take a longer time to process.
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
    _user: Optional["User"] = None

    # Relationships
    created_by = Relationship.ToOne("User", False, "created_by")
    organization = Relationship.ToOne("Organization")

    def refresh(self) -> None:
        """ Refreshes Task data from the server. """
        assert self._user is not None
        tasks = list(self._user.created_tasks(where=Task.uid == self.uid))
        if len(tasks) != 1:
            raise ResourceNotFoundError(Task, self.uid)
        for field in self.fields():
            setattr(self, field.name, getattr(tasks[0], field.name))

    def wait_till_done(self, timeout_seconds=300) -> None:
        """ Waits until the task is completed. Periodically queries the server
        to update the task attributes.

        Args:
            timeout_seconds (float): Maximum time this method can block, in seconds. Defaults to one minute.
        """
        check_frequency = 2  # frequency of checking, in seconds
        while True:
            if self.status != "IN_PROGRESS":
                return
            sleep_time_seconds = min(check_frequency, timeout_seconds)
            logger.debug("Task.wait_till_done sleeping for %.2f seconds" %
                         sleep_time_seconds)
            if sleep_time_seconds <= 0:
                break
            timeout_seconds -= check_frequency
            time.sleep(sleep_time_seconds)
            self.refresh()

    @property
    def errors(self) -> Optional[Dict[str, Any]]:
        """ Downloads the result file from Task
        """
        if self.status == "FAILED":
            result = self._fetch_remote_json()
            return result['error']
        return None

    @property
    def result(self) -> List[Dict[str, Any]]:
        """ Fetch the result for a task
        """
        if self.status == "FAILED":
            raise ValueError(f"Job failed. Errors : {self.errors}")
        else:
            result = self._fetch_remote_json()
            return [{
                'id': data_row['id'],
                'external_id': data_row.get('externalId'),
                'row_data': data_row['rowData']
            } for data_row in result['createdDataRows']]

    @lru_cache()
    def _fetch_remote_json(self) -> Dict[str, Any]:
        """ Function for fetching and caching the result data.
        """
        if self.name != 'JSON Import':
            raise ValueError(
                "Task result is only supported for `JSON Import` tasks."
                " Download task.result_url manually to access the result for other tasks."
            )
        self.wait_till_done(timeout_seconds=600)
        if self.status == "IN_PROGRESS":
            raise ValueError(
                "Job status still in `IN_PROGRESS`. The result is not available. Call task.wait_till_done() with a larger timeout or contact support."
            )

        response = requests.get(self.result_url)
        response.raise_for_status()
        return response.json()
