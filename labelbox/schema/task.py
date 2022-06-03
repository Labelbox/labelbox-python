import logging
import requests
import time
from typing import TYPE_CHECKING, Optional, Dict, Any
from functools import lru_cache

from labelbox.exceptions import ResourceNotFoundError
from labelbox.orm.db_object import DbObject
from labelbox.orm.model import Field, Relationship

if TYPE_CHECKING:
    from labelbox import User

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
        self.wait_till_done(timeout_seconds=600)
        if self.status == "FAILED":
            data = self._fetch_remote(self.result_url)
            if data:
                return data.get('error', None)
        elif self.status == "IN_PROGRESS":
            raise Exception("Job state IN_PROGRESS. Result not available.")
        return None

    @property
    def result(self) -> Dict[str, Any]:
        """ Fetch the result for a task
        """
        self.wait_till_done(timeout_seconds=600)
        if self.status == "COMPLETE":
            return self._fetch_remote(self.result_url)
        elif self.status == "FAILED":
            errors = self.errors
            message = errors.get('message') or errors
            raise Exception(f"Job failed. Errors : {message}")
        else:
            raise Exception("Job state IN_PROGRESS. Result not available.")

    @lru_cache()
    def _fetch_remote(self, result_url) -> Dict[str, Any]:
        """ Function for fetching and caching the result data.
        """
        response = requests.get(result_url)
        response.raise_for_status()
        return response.json()
