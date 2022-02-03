import threading
from queue import Queue
from typing import Any, Iterable

from labelbox.exceptions import ThreadException


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


class PrefetchThread(threading.Thread):
    """Class to override the Thread class. Helps raise 
    exceptions to the main caller thread
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.exc = None

    def run(self):
        try:
            super().run()
        except BaseException as e:
            self.exc = e

    def join(self, timeout=None):
        threading.Thread.join(self)
        if self.exc:
            raise self.exc


class PrefetchGenerator:
    """
    Applys functions asynchronously to the output of a generator.
    Useful for modifying the generator results based on data from a network
    """

    #maybe change num exec to just 1, and if 1, make sync
    #instead of self.get qeue in next, itll return just self._data.next
    #kwarg on export for multithread, and all other things that use prefetch

    def __init__(self,
                 data: Iterable[Any],
                 prefetch_limit=20,
                 num_executors=1,
                 multithread: bool = False):
        if isinstance(data, (list, tuple)):
            self._data = (r for r in data)
        else:
            self._data = data

        self.queue = Queue(prefetch_limit)
        self._data = ThreadSafeGen(self._data)
        self.completed_threads = 0
        # Can only iterate over once it the queue.get hangs forever.
        self.done = False
        if multithread:
            num_executors = 4
        self.num_executors = num_executors
        self.threads = [
            PrefetchThread(target=self.fill_queue) for _ in range(num_executors)
        ]
        for thread in self.threads:
            thread.daemon = True
            thread.start()
        for thread in self.threads:
            thread.join()

    def _process(self, value) -> Any:
        raise NotImplementedError("Abstract method needs to be implemented")

    def fill_queue(self):
        try:
            for value in self._data:
                value = self._process(value)
                if value is None:
                    raise ValueError("Unexpected None")
                self.queue.put(value)
        except:
            raise ThreadException(
                "Unexpected exception while filling the queue.")

    def __iter__(self):
        return self

    def __next__(self) -> Any:
        if self.done:
            raise StopIteration
        value = self.queue.get()
        while value is None:
            self.completed_threads += 1
            if self.completed_threads == self.num_executors:
                self.done = True
                for thread in self.threads:
                    thread.join()
                raise StopIteration
            value = self.queue.get()
        return value
