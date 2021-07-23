import logging
import threading
from queue import Queue
from typing import Any, Iterable
from concurrent.futures import ThreadPoolExecutor

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
        # Can only iterate over once it the queue.get hangs forever.
        self.done = False
        self.max_concurrency = max_concurrency
        with ThreadPoolExecutor(max_workers=max_concurrency) as executor:
            self.futures = [
                executor.submit(self.fill_queue) for _ in range(max_concurrency)
            ]

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
        if self.done:
            raise StopIteration
        value = self.queue.get()
        while value is None:
            self.completed_threads += 1
            if self.completed_threads == self.max_concurrency:
                self.done = True
                raise StopIteration
            value = self.queue.get()
        return value
