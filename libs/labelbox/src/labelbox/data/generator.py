import logging
import threading
from queue import Queue
from typing import Any, Iterable
import threading

logger = logging.getLogger(__name__)


class ThreadSafeGen:
    """
    Wraps generators to make them thread safe
    """

    def __init__(self, iterable: Iterable[Any]):
        """ """
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

    def __init__(self, data: Iterable[Any], prefetch_limit=20, num_executors=1):
        if isinstance(data, (list, tuple)):
            self._data = (r for r in data)
        else:
            self._data = data

        self.queue = Queue(prefetch_limit)
        self.completed_threads = 0
        # Can only iterate over once it the queue.get hangs forever.
        self.multithread = num_executors > 1
        self.done = False

        if self.multithread:
            self._data = ThreadSafeGen(self._data)
            self.num_executors = num_executors
            self.threads = [
                threading.Thread(target=self.fill_queue)
                for _ in range(num_executors)
            ]
            for thread in self.threads:
                thread.daemon = True
                thread.start()
        else:
            self._data = iter(self._data)

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
            self.queue.put(
                ValueError(f"Unexpected exception while filling queue: {e}")
            )
        finally:
            self.queue.put(None)

    def __iter__(self):
        return self

    def __next__(self) -> Any:
        if self.done:
            raise StopIteration

        if self.multithread:
            value = self.queue.get()

            while value is None:
                self.completed_threads += 1
                if self.completed_threads == self.num_executors:
                    self.done = True
                    for thread in self.threads:
                        thread.join()
                    raise StopIteration
                value = self.queue.get()
            if isinstance(value, Exception):
                raise value
        else:
            value = self._process(next(self._data))
        return value
