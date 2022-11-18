from typing import TYPE_CHECKING, List, Dict, Any, Union, Optional
from time import time
from datetime import datetime
from enum import Enum

class TaskStatus(Enum):
    SUBMITTED = 0
    COMPLETE = 1
    RUNNING = 2
    FAILED = 3
    RETRYING = 3

class TaskType(Enum):
    BEST_EFFORT = 0
    TRANSACTION = 1

class BaseTask:
    def __init__(self, task_id, object_class, metadata_query, query_name, created_at, expires_at = None):
        self._session = client

        self._metadata_query = metadata_query
        self._query_name = query_name
        self._task_id = task_id
        self.object_class = object_class

        self._status = None
        self._created_at = created_at
        self._expires_at = expires_at

        
    def status(self) -> Optional[TaskStatus]:
        # fetch if stale 
        if self._status is None or self.status == TaskStatus.RUNNING:
            self.__fetch_task_metadata()
        
        return self._status
 
    def wait_till_done(self):
        pass
 
    def created_at(self) -> time:
        return self._created_at
 
    def expires_at(self) -> Optional[time]:
        pass

    def __fetch_task_metadata(self):
        response = self._session.execute(self._metadata_query, {TASK_ID_KEY: self.task_id})
        self.task_status = response[TASK_STATUS_KEY]


class Task(BaseTask): 
    def error(self) -> Optional[BaseError]:
        pass
 
    def result(self) -> Optional[BaseObject]:
        pass

class BulkTask(BaseTask):
    def __init__(
        self, 
        task_id, 
        object_class,
        task_type = TaskType.TRANSACTION,
        query = DEFAULT_QUERY, 
        query_name = DEFAULT_QUERY_NAME, 
        created_at = datetime.now()
    ):
        super(BaseTask, self).__init__(task_id, query, query_name, created_at, object_class)
        self.results_iterator = None
        self.errors_iterator = None

    def results(self) -> Optional[FetchingIterator]:
        if self.status() == TaskStatus.COMPLETE:
            if self.results_iterator:
                return self.results_iterator

            self.results_iterator = FetchingIterator()
        return None
 
    def errors(self) -> FetchingIterator:
        if self.status() != TaskStatus.SUBMITTED and self.status() != TaskStatus.RUNNING:
            if self.errors_iterator:
                return self.errors_iterator

            self.errors_iterator = FetchingIterator()
        return None
 
    @property
    def kind(self) -> TaskType:
        return self.task_type
