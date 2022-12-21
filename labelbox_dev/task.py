import json
import logging
import time
from abc import ABC, abstractmethod
from enum import Enum
from functools import lru_cache
from typing import Any, Dict, Union

import requests

from labelbox_dev.entity import Entity
from labelbox_dev.exceptions import ResourceNotFoundError
from labelbox_dev.session import Session
from labelbox_dev.utils import format_json_to_snake_case

TASK_RESOURCE = "tasks"

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    IN_PROGRESS = "IN_PROGRESS"


class TaskType(Enum):
    CREATE_DATA_ROWS = "CREATE_DATA_ROWS"
    BULK_GET_DATA_ROWS = "BULK_GET_DATA_ROWS"


class BaseTask(Entity, ABC):
    """ Abstract class representing an asynchronous task
    """

    task_type: TaskType

    def __init__(self, json):
        super().__init__(json)
        self.from_json(json)

    def from_json(self, json) -> "BaseTask":
        super().from_json(json)
        self.id = self.json['id']
        self.status = self.json['status']
        self.updated_at = self.json.get('updated_at')
        self.created_at = self.json.get('created_at')
        self.name = self.json.get('name')
        self.completion_percentage = self.json.get('completion_percentage')
        self.result_url = self.json.get('result_url')

    @classmethod
    def get_by_id(cls, task_id) -> "BaseTask":
        task_json = Session.get_request(f"{TASK_RESOURCE}/{task_id}",
                                        {'task_type': cls.task_type.name})
        return cls(task_json)

    def refresh(self) -> "BaseTask":
        task_json = Session.get_request(f"{TASK_RESOURCE}/{self.id}",
                                        {'task_type': self.task_type.name})
        return self.from_json(task_json)

    @abstractmethod
    def wait_until_done(self):
        ...


class Task(BaseTask, ABC):
    """ Abstract class representing an asynchronous task with single input.
    Users can call `task.result` and `task.error` to obtain either the
    job result upon success, or job error upon failure, respectively.
    """

    def __init__(self, json):
        super().__init__(json)

    @property
    @abstractmethod
    def result(self):
        ...

    @property
    @abstractmethod
    def error(self):
        ...


class BulkTask(BaseTask, ABC):
    """ Abstract class representing an asynchronous task with bulk input.
    Users can call `task.results` and `task.errors` to obtain either the
    job results upon success, or job errors upon failure.
    """

    def __init__(self, json):
        super().__init__(json)

    @property
    @abstractmethod
    def results(self):
        ...

    @property
    @abstractmethod
    def errors(self):
        ...

    def wait_until_done(self, timeout_seconds=300) -> "TaskStatus":
        assert self.id is not None
        check_frequency = 2  # frequency of checking, in seconds
        while True:
            if self.status != TaskStatus.IN_PROGRESS.name:
                if self.errors is not None:
                    logger.warning(
                        "There are errors present. Please look at `task.errors` for more details"
                    )
                    return TaskStatus.FAILED
                else:
                    return TaskStatus.COMPLETE
            sleep_time_seconds = min(check_frequency, timeout_seconds)
            logger.debug("Task.wait_till_done sleeping for %.2f seconds" %
                         sleep_time_seconds)
            if sleep_time_seconds <= 0:
                if self.status == TaskStatus.IN_PROGRESS.name:
                    raise TimeoutError(
                        "`task.wait_until_done()` has timed out before Task has finished. Please call `task.wait_until_done()` with a larger timeout or contact support."
                    )
                return TaskStatus.IN_PROGRESS
            timeout_seconds -= check_frequency
            time.sleep(sleep_time_seconds)
            self.refresh()


class BulkGetDataRowsTask(BulkTask):
    task_type = TaskType.BULK_GET_DATA_ROWS

    def __init__(self, json):
        super().__init__(json)

    @lru_cache()
    def fetch_result(self) -> Dict[str, Any]:
        if self.status == TaskStatus.IN_PROGRESS.name:
            raise ResourceNotFoundError(
                f"Task result for task '{self.id}' not found. Task is still in progress"
            )
        else:
            response = requests.get(self.result_url)
            response.raise_for_status()
            return response.json()

    @property
    def results(self) -> Union[Dict[str, Any], None]:
        task_result = self.fetch_result()
        if self.status == TaskStatus.FAILED.name or 'results' not in task_result:
            logger.warning(
                "Task has failed. Please look at `task.errors` for more details"
            )
            return None

        result = {}
        # TODO: Format results as DataRow objects
        result['data_rows'] = [
            format_json_to_snake_case(dr) for dr in task_result['results']
        ]
        return result

    @property
    def errors(self):
        task_result = self.fetch_result()
        errors = {}
        if 'errors' in task_result and len(task_result['errors']) != 0:
            errors['errors'] = task_result['errors']

        return errors if errors else None


class CreateDataRowsTask(BulkTask):
    """ Asynchronous task representing bulk data_row create job
    """

    task_type = TaskType.CREATE_DATA_ROWS

    def __init__(self, json):
        super().__init__(json)

    @lru_cache()
    def fetch_result(self) -> Dict[str, Any]:
        if self.status == TaskStatus.IN_PROGRESS.name:
            raise ResourceNotFoundError(
                f"Task result for task '{self.id}' not found. Task is still in progress"
            )
        else:
            response = requests.get(self.result_url)
            response.raise_for_status()
            return response.json()

    # TODO: Need to paginate results
    @property
    def results(self) -> Union[Dict[str, Any], None]:
        task_result = self.fetch_result()
        if self.status == TaskStatus.FAILED.name or 'createdDataRows' not in task_result:
            logger.warning(
                "Task has failed. Please look at `task.errors` for more details"
            )
            return None

        result = {}
        result['created_data_rows'] = [
            format_json_to_snake_case(dr)
            for dr in task_result['createdDataRows']
        ]
        return result

    @property
    def errors(self) -> Union[Dict[str, Any], None]:
        task_result = self.fetch_result()
        # TODO: Improve error message from backend
        errors = {}
        if 'errors' in task_result and len(task_result['errors']) != 0:
            errors['errors'] = task_result['errors']
        if 'failedDataRows' in task_result:
            errors['failed_data_rows'] = task_result['failedDataRows']

        return errors if errors else None
