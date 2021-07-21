import logging
import threading
from queue import Queue
from typing import Any, Iterable

logger = logging.getLogger(__name__)


class ThreadSafeGen:
    """
    Wraps generators to make them thread safe
    """

    def __init__(self, iterable: Iterable[Any]):
        """

        """
        self.iterable = iterable
        self.lock = threading.Lock()

    def __iter__(self):
        return self

    def __next__(self):
        with self.lock:
            return next(self.iterable)


class PrefetchGenerator:
    """
    Applys functions asynchronously to the output of a generator.
    Useful for modifying the generator results based on data from a network
    """

    def __init__(self,
                 data: Iterable[Any],
                 prefetch_limit=20,
                 max_concurrency=4):
        if isinstance(data, (list, tuple)):
            self._data = (r for r in data)
        else:
            self._data = data

        self.queue = Queue(prefetch_limit)
        self._data = ThreadSafeGen(self._data)
        self.completed_threads = 0
        self.max_concurrency = max_concurrency
        self.threads = [
            threading.Thread(target=self.fill_queue)
            for _ in range(max_concurrency)
        ]
        for thread in self.threads:
            thread.daemon = True
            thread.start()

    def _process(self, value) -> Any:
        raise NotImplementedError("Abstract method needs to be implemented")

    def fill_queue(self):
        try:
            for value in self._data:
                value = self._process(value)
                if value is None:
                    raise ValueError("Unexpected None")
                self.queue.put(value)
        except Exception as e:
            logger.warning("Unexpected exception while filling the queue. %r",
                           e)
        finally:
            self.queue.put(None)

    def __iter__(self):
        return self

    def __next__(self) -> Any:
        value = self.queue.get()
        while value is None:
            self.completed_threads += 1
            if self.completed_threads == self.max_concurrency:
                raise StopIteration
            value = self.queue.get()
        return value
