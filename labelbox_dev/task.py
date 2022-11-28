from typing import TYPE_CHECKING, List, Dict, Any, Union, Optional
from time import time
from datetime import datetime
from enum import Enum
from fetching_iterator import FetchingIterator
from labelbox_dev.entity import Entity
from labelbox_dev.fetching_iterator import TOTAL_PAGES_KEY
from labelbox_dev.session import Session
from labelbox_dev.errors import BaseError
class TaskStatus(Enum):
    SUBMITTED = 0
    COMPLETE = 1
    RUNNING = 2
    FAILED = 3
    RETRYING = 3

class TaskType(Enum):
    BEST_EFFORT = 0
    TRANSACTION = 1


ASYNCOPERATIONS_RESOURCE = "asyncoperations"
TASK_STATUS_KEY = 'jobStatus'
TOTAL_RESULT_PAGES_KEY = 'totalResultPages'
TOTAL_ERROR_PAGES_KEY = 'totalErrorPages'

class BaseTask:
    def __init__(self, task_id, object_class, created_at, expires_at = None):
        self._task_id = task_id
        self._object_class = object_class

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
    
    def __parse_task_metadata(self, page_response):
        return page_response.get(TASK_STATUS_KEY)

    def __fetch_task_metadata(self):
        page_response = Session.get_request(f'{ASYNCOPERATIONS_RESOURCE}/{self.task_id}/')
        self.task_status = self.__parse_task_metadata(page_response)


class Task(BaseTask): 
    def error(self) -> Optional[BaseError]:
        pass
 
    def result(self) -> Optional[Entity]:
        pass

class BulkTask(BaseTask):
    def __init__(
        self, 
        task_id, 
        object_class,
        task_type = TaskType.TRANSACTION,
        created_at = datetime.now()
    ):
        super(BaseTask, self).__init__(task_id, created_at, object_class)
        self._results_iterator = None
        self._total_results_pages = None
        self._errors_iterator = None
        self._total_error_pages = None
        self._task_type = task_type

    def results(self) -> Optional[FetchingIterator]:
        if self.status() != TaskStatus.COMPLETE:
            return None
        
        if self._results_iterator:
            return self._results_iterator

        self._results_iterator = FetchingIterator(
            object_class = self.object_class,
            query = f"{ASYNCOPERATIONS_RESOURCE}/{self._task_id}/results",
            task_id = self._task_id,
            total_pages = self._total_results_pages
        )

        return self._results_iterator
 
    def errors(self) -> FetchingIterator:
        if self.status() == TaskStatus.SUBMITTED or self.status() != TaskStatus.RUNNING:
            return None
        
        if self.errors_iterator:
            return self.errors_iterator

        self._errors_iterator = FetchingIterator(
            object_class = BaseError,
            query = f"{ASYNCOPERATIONS_RESOURCE}/{self._task_id}/errors",
            task_id = self._task_id,
            total_pages = self._total_error_pages
        )

        return self._results_iterator
 
    @property
    def kind(self) -> TaskType:
        return self.task_type

    def __parse_task_metadata(self, page_response):
        self._status = page_response.get(TASK_STATUS_KEY)
        self._total_pages = page_response.get(TOTAL_PAGES_KEY)



    def __fetch_task_metadata(self):
        page_response = Session.get_request(f'{ASYNCOPERATIONS_RESOURCE}/{self.task_id}/')
        self.__parse_task_metadata(page_response)
