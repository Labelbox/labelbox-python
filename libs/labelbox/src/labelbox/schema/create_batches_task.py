import json
from typing import TYPE_CHECKING, Callable, List, Optional, Dict, Any

from labelbox.orm.model import Entity

if TYPE_CHECKING:
    from labelbox import User

    def lru_cache() -> Callable[..., Callable[..., Dict[str, Any]]]:
        pass
else:
    from functools import lru_cache


class CreateBatchesTask:

    def __init__(self, client, project_id: str, batch_ids: List[str],
                 task_ids: List[str]):
        self.client = client
        self.project_id = project_id
        self.batches = batch_ids
        self.tasks = [
            Entity.Task.get_task(self.client, task_id) for task_id in task_ids
        ]

    def wait_until_done(self, timeout_seconds: int = 300) -> None:
        self.wait_till_done(timeout_seconds)

    def wait_till_done(self, timeout_seconds: int = 300) -> None:
        """
        Waits for the task to complete.

        Args:
            timeout_seconds: the number of seconds to wait before timing out

        Returns: None
        """

        for task in self.tasks:
            task.wait_till_done(timeout_seconds)

    def errors(self) -> Optional[Dict[str, Any]]:
        """
        Returns the errors from the task, if any.

        Returns: a dictionary of errors, keyed by task id
        """

        errors = {}
        for task in self.tasks:
            if task.status == "FAILED":
                errors[task.uid] = json.loads(task.result_url)

        if len(errors) == 0:
            return None

        return errors

    @lru_cache()
    def result(self):
        """
        Returns the batches created by the task.

        Returns: the list of batches created by the task
        """

        return [
            self.client.get_batch(self.project_id, batch_id)
            for batch_id in self.batches
        ]
